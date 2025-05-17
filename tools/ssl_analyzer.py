import socket
import ssl
import datetime
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from urllib.parse import urlparse

from .tool_decorator import recon_tool

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ssl_analyzer")

# SSL/TLS protocols to test
SSL_PROTOCOLS = {
    'SSLv2': ssl.PROTOCOL_SSLv23,
    'SSLv3': ssl.PROTOCOL_SSLv23,
    'TLSv1': ssl.PROTOCOL_TLSv1,
    'TLSv1.1': ssl.PROTOCOL_TLSv1_1,
    'TLSv1.2': ssl.PROTOCOL_TLSv1_2,
    'TLSv1.3': ssl.PROTOCOL_TLS,
}

# Cipher strengths classification
WEAK_CIPHERS = [
    'RC4', 'DES', 'NULL', 'EXP', 'ADH', 'IDEA', 'MD5', 'SHA1', '3DES'
]

@recon_tool
def analyze_ssl_tls(url: str, timeout: int = 10, check_cert_info: bool = True, 
                  check_protocols: bool = True, check_ciphers: bool = True) -> Dict[str, Any]:
    """
    Analyzes SSL/TLS configuration of a web server for security issues.
    
    Args:
        url: The URL to analyze SSL/TLS configuration for
        timeout: Connection timeout in seconds
        check_cert_info: Whether to check certificate information
        check_protocols: Whether to check supported protocols
        check_ciphers: Whether to check for weak ciphers
        
    Returns:
        Dictionary with SSL/TLS analysis results
    """
    # Ensure the URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Parse the URL to get hostname and port
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc.split(':')[0]
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    
    results = {
        'target': url,
        'hostname': hostname,
        'port': port,
        'cert_info': {},
        'supported_protocols': {},
        'cipher_strength': {
            'strong_ciphers': [],
            'weak_ciphers': [],
        },
        'issues': [],
        'summary': {},
    }
    
    # Check if it's not HTTPS
    if parsed_url.scheme != 'https':
        results['issues'].append('Target is not using HTTPS')
        results['summary'] = {
            'is_secure': False,
            'grade': 'F',
            'recommendations': ['Implement HTTPS']
        }
        return results
    
    # Certificate information
    if check_cert_info:
        try:
            cert_info = _get_certificate_info(hostname, port, timeout)
            results['cert_info'] = cert_info
            
            # Check for certificate issues
            if cert_info.get('expired', False):
                results['issues'].append('SSL Certificate has expired')
            
            if not cert_info.get('valid_hostname', True):
                results['issues'].append('SSL Certificate hostname validation failed')
                
            if cert_info.get('self_signed', False):
                results['issues'].append('Self-signed certificate detected')
                
            if cert_info.get('days_remaining', 0) < 30:
                results['issues'].append(f'Certificate expiring soon: {cert_info.get("days_remaining")} days remaining')
                
            if cert_info.get('signature_algorithm', '').endswith('WithRSA'):
                if 'MD5' in cert_info.get('signature_algorithm', ''):
                    results['issues'].append('Weak signature algorithm: MD5')
                elif 'SHA1' in cert_info.get('signature_algorithm', ''):
                    results['issues'].append('Weak signature algorithm: SHA1')
                    
        except Exception as e:
            logger.error(f"Error checking certificate: {str(e)}")
            results['issues'].append(f'Error checking certificate: {str(e)}')
    
    # Protocol support
    if check_protocols:
        try:
            supported_protocols = _check_supported_protocols(hostname, port, timeout)
            results['supported_protocols'] = supported_protocols
            
            # Check for protocol issues
            if supported_protocols.get('SSLv2', False):
                results['issues'].append('Deprecated protocol supported: SSLv2')
                
            if supported_protocols.get('SSLv3', False):
                results['issues'].append('Deprecated protocol supported: SSLv3')
                
            if supported_protocols.get('TLSv1', False):
                results['issues'].append('Outdated protocol supported: TLSv1.0')
                
            if supported_protocols.get('TLSv1.1', False):
                results['issues'].append('Outdated protocol supported: TLSv1.1')
                
            if not supported_protocols.get('TLSv1.2', False) and not supported_protocols.get('TLSv1.3', False):
                results['issues'].append('No secure protocols (TLSv1.2, TLSv1.3) supported')
                
        except Exception as e:
            logger.error(f"Error checking protocols: {str(e)}")
            results['issues'].append(f'Error checking protocols: {str(e)}')
    
    # Cipher strength
    if check_ciphers:
        try:
            strong_ciphers, weak_ciphers = _check_cipher_strength(hostname, port, timeout)
            results['cipher_strength']['strong_ciphers'] = strong_ciphers
            results['cipher_strength']['weak_ciphers'] = weak_ciphers
            
            # Check for cipher issues
            if weak_ciphers:
                results['issues'].append(f'Weak ciphers detected: {", ".join(weak_ciphers[:5])}' + 
                                       (f' and {len(weak_ciphers) - 5} more' if len(weak_ciphers) > 5 else ''))
                
        except Exception as e:
            logger.error(f"Error checking ciphers: {str(e)}")
            results['issues'].append(f'Error checking ciphers: {str(e)}')
    
    # Generate overall security grade
    grade = _calculate_security_grade(results)
    recommendations = _generate_recommendations(results)
    
    results['summary'] = {
        'is_secure': grade in ['A+', 'A', 'A-', 'B+', 'B'],
        'grade': grade,
        'recommendations': recommendations
    }
    
    return results

def _get_certificate_info(hostname: str, port: int, timeout: int) -> Dict[str, Any]:
    """Get detailed information about the SSL certificate."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert(binary_form=True)
            x509 = ssl.DER_cert_to_PEM_cert(cert)
            cert_dict = ssock.getpeercert()
            
            # Get certificate details
            not_before = datetime.datetime.strptime(cert_dict['notBefore'], "%b %d %H:%M:%S %Y %Z")
            not_after = datetime.datetime.strptime(cert_dict['notAfter'], "%b %d %H:%M:%S %Y %Z")
            now = datetime.datetime.utcnow()
            
            # Check if expired
            expired = now > not_after
            days_remaining = (not_after - now).days
            
            # Get issuer
            issuer = {}
            for item in cert_dict.get('issuer', []):
                for key, value in item:
                    if key == 'organizationName':
                        issuer['organization'] = value
                    elif key == 'commonName':
                        issuer['common_name'] = value
            
            # Get subject
            subject = {}
            for item in cert_dict.get('subject', []):
                for key, value in item:
                    if key == 'commonName':
                        subject['common_name'] = value
                    elif key == 'organizationName':
                        subject['organization'] = value
            
            # Check if self-signed
            self_signed = False
            if issuer.get('common_name') == subject.get('common_name') and issuer.get('organization') == subject.get('organization'):
                self_signed = True
            
            # Check if hostname matches certificate
            valid_hostname = False
            if 'subjectAltName' in cert_dict:
                for alt_type, alt_name in cert_dict['subjectAltName']:
                    if alt_type == 'DNS' and (alt_name == hostname or alt_name.startswith('*.')):
                        valid_hostname = True
                        break
            
            # Certificate algorithm
            signature_algorithm = "Unknown"
            try:
                # Attempt to get algorithm info from OpenSSL output
                # This is not always available in the standard library
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                cert_obj = x509.load_pem_x509_certificate(x509.encode(), default_backend())
                signature_algorithm = cert_obj.signature_algorithm_oid._name
            except ImportError:
                # Fall back to basic info
                signature_algorithm = "Unable to determine (cryptography library not available)"
            
            return {
                'issuer': issuer,
                'subject': subject,
                'valid_from': not_before.isoformat(),
                'valid_until': not_after.isoformat(),
                'days_remaining': days_remaining,
                'expired': expired,
                'self_signed': self_signed,
                'valid_hostname': valid_hostname,
                'signature_algorithm': signature_algorithm
            }

def _check_supported_protocols(hostname: str, port: int, timeout: int) -> Dict[str, bool]:
    """Check which SSL/TLS protocols are supported by the server."""
    results = {}
    
    for protocol_name, protocol in SSL_PROTOCOLS.items():
        try:
            context = ssl.SSLContext(protocol)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            if protocol_name == 'SSLv2':
                # Try to explicitly enable SSLv2 (likely to fail on modern Python)
                try:
                    context.options &= ~ssl.OP_NO_SSLv2
                except AttributeError:
                    pass
            
            if protocol_name == 'SSLv3':
                # Try to explicitly enable SSLv3
                try:
                    context.options &= ~ssl.OP_NO_SSLv3
                except AttributeError:
                    pass
            
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                try:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        results[protocol_name] = True
                except ssl.SSLError:
                    results[protocol_name] = False
        except (socket.error, ssl.SSLError, ConnectionResetError, ConnectionRefusedError, TimeoutError):
            results[protocol_name] = False
        except Exception as e:
            logger.error(f"Error checking protocol {protocol_name}: {str(e)}")
            results[protocol_name] = False
    
    return results

def _check_cipher_strength(hostname: str, port: int, timeout: int) -> Tuple[List[str], List[str]]:
    """Check the strength of supported ciphers."""
    strong_ciphers = []
    weak_ciphers = []
    
    # Try modern protocol first
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.set_ciphers("ALL:@SECLEVEL=0")
    
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                current_cipher = ssock.cipher()
                if current_cipher:
                    # Check if the cipher is considered weak
                    cipher_name = current_cipher[0]
                    cipher_protocol = current_cipher[1]
                    if any(weak in cipher_name for weak in WEAK_CIPHERS):
                        weak_ciphers.append(f"{cipher_name} ({cipher_protocol})")
                    else:
                        strong_ciphers.append(f"{cipher_name} ({cipher_protocol})")
    except Exception as e:
        logger.error(f"Error checking cipher strength: {str(e)}")
    
    # For comprehensive cipher checking, we would ideally use a library like 'cryptography'
    # or an external tool like OpenSSL or sslyze, but that's beyond the scope of this basic check
    
    return strong_ciphers, weak_ciphers

def _calculate_security_grade(results: Dict[str, Any]) -> str:
    """Calculate an overall security grade based on the analysis results."""
    # Count issues by severity
    critical_issues = 0
    high_issues = 0
    medium_issues = 0
    low_issues = 0
    
    for issue in results['issues']:
        if any(x in issue for x in ['expired', 'SSLv2', 'SSLv3', 'MD5']):
            critical_issues += 1
        elif any(x in issue for x in ['TLSv1.0', 'TLSv1.1', 'self-signed', 'validation failed']):
            high_issues += 1
        elif any(x in issue for x in ['Weak cipher', 'SHA1']):
            medium_issues += 1
        else:
            low_issues += 1
    
    # Determine grade
    if critical_issues == 0 and high_issues == 0 and medium_issues == 0 and low_issues == 0:
        if results['supported_protocols'].get('TLSv1.3', False):
            return 'A+'
        else:
            return 'A'
    elif critical_issues == 0 and high_issues == 0 and medium_issues == 0:
        return 'A-'
    elif critical_issues == 0 and high_issues == 0:
        return 'B+'
    elif critical_issues == 0 and high_issues <= 1:
        return 'B'
    elif critical_issues == 0:
        return 'C'
    elif critical_issues <= 1:
        return 'D'
    else:
        return 'F'

def _generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate security recommendations based on the issues found."""
    recommendations = []
    
    # Certificate recommendations
    if results.get('cert_info', {}).get('expired', False):
        recommendations.append("Renew the expired SSL certificate immediately")
    
    if results.get('cert_info', {}).get('self_signed', False):
        recommendations.append("Replace self-signed certificate with one from a trusted CA")
    
    if results.get('cert_info', {}).get('days_remaining', 999) < 30:
        recommendations.append(f"Renew certificate soon (expires in {results.get('cert_info', {}).get('days_remaining', 0)} days)")
    
    # Protocol recommendations
    protocols = results.get('supported_protocols', {})
    if protocols.get('SSLv2', False):
        recommendations.append("Disable SSLv2 protocol (critical)")
    
    if protocols.get('SSLv3', False):
        recommendations.append("Disable SSLv3 protocol (critical)")
    
    if protocols.get('TLSv1', False):
        recommendations.append("Disable TLSv1.0 protocol (high)")
    
    if protocols.get('TLSv1.1', False):
        recommendations.append("Disable TLSv1.1 protocol (medium)")
    
    if not protocols.get('TLSv1.2', False) and not protocols.get('TLSv1.3', False):
        recommendations.append("Enable TLSv1.2 and TLSv1.3 protocols (critical)")
    elif not protocols.get('TLSv1.3', False):
        recommendations.append("Enable TLSv1.3 protocol for better security (low)")
    
    # Cipher recommendations
    if results.get('cipher_strength', {}).get('weak_ciphers', []):
        recommendations.append("Disable weak ciphers: " + 
                             ", ".join(results.get('cipher_strength', {}).get('weak_ciphers', [])[:3]) +
                             (", and others" if len(results.get('cipher_strength', {}).get('weak_ciphers', [])) > 3 else ""))
    
    # If no specific recommendations, add general one
    if not recommendations:
        recommendations.append("Configuration looks good, maintain current security settings")
    
    return recommendations

# Example usage
if __name__ == "__main__":
    results = analyze_ssl_tls("example.com")
    print(json.dumps(results, indent=2)) 