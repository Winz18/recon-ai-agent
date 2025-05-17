import httpx
import re
import json
import logging
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .tool_decorator import recon_tool

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cms_detector")

# CMS Fingerprints
CMS_FINGERPRINTS = {
    'WordPress': {
        'headers': [],
        'cookies': ['wordpress_', 'wp-settings-'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'WordPress\s*([\d.]+)?'},
        ],
        'paths': [
            '/wp-login.php',
            '/wp-admin/',
            '/wp-content/',
            '/wp-includes/',
            '/xmlrpc.php',
            '/wp-json/',
        ],
        'regex_patterns': [
            r'wp-(?:content|includes)',
            r'\/wp-content\/plugins\/',
            r'\/wp-content\/themes\/',
            r'wordpress_(?:test_cookie|logged_in|sec)',
        ],
        'version_paths': [
            {
                'path': '/readme.html',
                'regex': r'<br\s*\/>\s*[Vv]ersion\s*([\d.]+)'
            },
            {
                'path': '/feed/',
                'regex': r'<generator>https?:\/\/wordpress\.org\/\?v=([\d.]+)<\/generator>'
            },
        ]
    },
    'Drupal': {
        'headers': [],
        'cookies': ['SESS', 'Drupal.tableDrag.showWeight'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Drupal\s*([\d.]+)'},
        ],
        'paths': [
            '/user/login/',
            '/admin/',
            '/sites/default/',
            '/misc/drupal.js',
            '/CHANGELOG.txt',
            '/core/CHANGELOG.txt',
            '/includes/',
            '/misc/',
            '/modules/',
            '/sites/',
            '/themes/',
        ],
        'regex_patterns': [
            r'Drupal.settings',
            r'sites\/all\/(themes|modules)',
            r'drupal.org',
        ],
        'version_paths': [
            {
                'path': '/CHANGELOG.txt',
                'regex': r'Drupal\s*([\d.]+)'
            },
            {
                'path': '/core/CHANGELOG.txt',
                'regex': r'Drupal\s*([\d.]+)'
            },
        ]
    },
    'Joomla': {
        'headers': [],
        'cookies': ['joomla_', 'jpanesliders_'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Joomla!?\s*([\d.]+)?'},
        ],
        'paths': [
            '/administrator/',
            '/components/',
            '/modules/',
            '/templates/',
            '/media/',
            '/language/',
            '/plugins/',
            '/includes/'
        ],
        'regex_patterns': [
            r'\/templates\/system\/',
            r'\/media\/system\/js\/',
            r'com_content',
            r'Joomla!',
        ],
        'version_paths': [
            {
                'path': '/language/en-GB/en-GB.xml',
                'regex': r'<version>([\d.]+)'
            },
            {
                'path': '/administrator/manifests/files/joomla.xml',
                'regex': r'<version>([\d.]+)'
            },
        ]
    },
    'Magento': {
        'headers': [],
        'cookies': ['mage-cache-', 'mage-translation-'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Magento'},
        ],
        'paths': [
            '/app/etc/',
            '/js/mage/',
            '/skin/',
            '/media/catalog/',
            '/index.php/admin/',
            '/catalog/product_compare/',
            '/checkout/cart/',
            '/customer/account/'
        ],
        'regex_patterns': [
            r'var BLANK_URL = \'.*\/js\/blank\.html',
            r'var BLANK_IMG = \'.*\/js\/spacer\.gif',
            r'Mage.Cookies.path',
            r'Magento_',
        ],
        'version_paths': [
            {
                'path': '/magento_version',
                'regex': r'([\d.]+)'
            },
            {
                'path': '/js/varien/product.js',
                'regex': r'@author\s+Magento Team.+@copyright\s+Copyright \(c\) ([\d]+-[\d]+)'
            },
        ]
    },
    'Shopify': {
        'headers': [
            {'name': 'X-ShopId', 'regex': r'.+'},
            {'name': 'X-Shopify-Stage', 'regex': r'.+'},
        ],
        'cookies': ['_shopify_'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Shopify'},
        ],
        'paths': [
            '/collections/',
            '/products/',
            '/cart/',
            '/account/',
            '/apps/',
            '/policies/',
        ],
        'regex_patterns': [
            r'Shopify.theme',
            r'Shopify\.(?:shop|locale|currency|customer|cart)',
            r'cdn\.shopify\.com',
            r'shopify\.com\/s\/',
        ],
        'version_paths': []
    },
    'Ghost': {
        'headers': [],
        'cookies': ['ghost-admin-api-session'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Ghost\s*([\d.]+)'},
        ],
        'paths': [
            '/ghost/',
            '/content/images/',
            '/assets/ghost.js',
            '/content/themes/',
        ],
        'regex_patterns': [
            r'ghost-(?:url|path|version)',
            r'content/themes/(?:casper)',
            r'ghost-frontend',
        ],
        'version_paths': [
            {
                'path': '/ghost/api/admin/site/',
                'regex': r'"version":"([\d.]+)"'
            },
        ]
    },
    'Laravel': {
        'headers': [],
        'cookies': ['laravel_session'],
        'meta_tags': [],
        'paths': [
            '/vendor/laravel/',
            '/public/vendor/laravel/',
            '/storage/logs/',
            '/artisan',
        ],
        'regex_patterns': [
            r'laravel_session',
            r'laravel-validation-error',
            r'Laravel\s*[=:]',
            r'csrf-token',
        ],
        'version_paths': []
    },
    'Django': {
        'headers': [],
        'cookies': ['csrftoken', 'sessionid', 'django_'],
        'meta_tags': [],
        'paths': [
            '/admin/login/',
            '/static/admin/',
            '/media/admin/',
        ],
        'regex_patterns': [
            r'__all__',
            r'csrfmiddlewaretoken',
            r'adminform',
            r'(?:Django|DJANGO)',
        ],
        'version_paths': []
    },
    'Wix': {
        'headers': [],
        'cookies': [],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Wix.com'},
        ],
        'paths': [],
        'regex_patterns': [
            r'X-Wix-',
            r'static\.wixstatic\.com',
            r'wix-instantsearchplus',
            r'wix-dropdown-menu',
        ],
        'version_paths': []
    },
    'Squarespace': {
        'headers': [],
        'cookies': ['SS_MID', 'SQSP_'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Squarespace'},
        ],
        'paths': [
            '/api/1/performance/',
            '/commerce/digital-download/',
            '/commerce/checkout/',
            '/servlet/'
        ],
        'regex_patterns': [
            r'static[0-9]\.squarespace\.com',
            r'squarespace\.com',
            r'SQUARESPACE_CONTEXT',
        ],
        'version_paths': []
    },
    'PrestaShop': {
        'headers': [],
        'cookies': ['PrestaShop-'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'PrestaShop\s*([\d.]+)?'},
        ],
        'paths': [
            '/modules/',
            '/admin/',
            '/themes/',
            '/img/',
            '/js/jquery/plugins/',
            '/tools/swift/Swift/Cache/Cache.php',
        ],
        'regex_patterns': [
            r'var\s+prestashop\s*=',
            r'presta(?:shop|Pay)',
            r'modules\/ps_',
        ],
        'version_paths': [
            {
                'path': '/modules/autoupgrade/config.xml',
                'regex': r'<version><!\[CDATA\[([\d.]+)'
            },
        ]
    },
    'Webflow': {
        'headers': [],
        'cookies': [],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'Webflow'},
        ],
        'paths': [],
        'regex_patterns': [
            r'webflow-(?:badge|js)',
            r'uploads-ssl\.webflow\.com',
            r'typedlink\.webflow\.io',
            r'assets-global\.website-files\.com',
        ],
        'version_paths': []
    },
    'OpenCart': {
        'headers': [],
        'cookies': ['OCSESSID'],
        'meta_tags': [],
        'paths': [
            '/admin/',
            '/catalog/',
            '/system/',
            '/image/',
            '/index.php?route=common/',
            '/download/',
        ],
        'regex_patterns': [
            r'index\.php\?route=',
            r'catalog\/view\/theme',
            r'OpenCart',
        ],
        'version_paths': [
            {
                'path': '/index.php?route=common/home',
                'regex': r'OpenCart\s+([\d.]+)'
            },
        ]
    },
    'TYPO3': {
        'headers': [],
        'cookies': ['be_typo_user'],
        'meta_tags': [
            {'name': 'generator', 'content_regex': r'TYPO3\s*([\d.]+)'},
        ],
        'paths': [
            '/typo3/',
            '/typo3conf/',
            '/typo3temp/',
            '/fileadmin/',
        ],
        'regex_patterns': [
            r'typo3conf\/ext\/',
            r'typo3temp\/',
            r'typo3_src',
        ],
        'version_paths': [
            {
                'path': '/typo3/README.md',
                'regex': r'TYPO3\s+CMS\s+([\d.]+)'
            },
        ]
    }
}

@recon_tool
async def detect_cms(url: str, deep_scan: bool = False, timeout: int = 10) -> Dict[str, Any]:
    """
    Detects the Content Management System (CMS) used by a website.
    
    Args:
        url: The URL of the website to scan
        deep_scan: Whether to perform a deeper scan for version information
        timeout: Connection timeout in seconds
        
    Returns:
        Dictionary with CMS detection results
    """
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Initialize results dictionary
    results = {
        'target': url,
        'detected_cms': None,
        'confidence': 0,
        'version': None,
        'version_confidence': 0,
        'evidence': [],
        'detected_plugins': [],
        'detected_themes': [],
        'technologies': [],
        'additional_info': {},
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # Request the main page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'close',
            }
            
            response = await client.get(url, headers=headers)
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Dictionary to store match counts for each CMS
            cms_matches = {}
            cms_evidence = {}
            
            # Check each CMS fingerprints
            for cms, fingerprints in CMS_FINGERPRINTS.items():
                cms_matches[cms] = 0
                cms_evidence[cms] = []
                
                # 1. Check HTTP headers
                for header in fingerprints['headers']:
                    header_name = header['name'].lower()
                    header_regex = header['regex']
                    
                    for resp_header, value in response.headers.items():
                        if resp_header.lower() == header_name and re.search(header_regex, value, re.I):
                            cms_matches[cms] += 1
                            cms_evidence[cms].append(f'Header {resp_header}: {value}')
                
                # 2. Check cookies
                for cookie_pattern in fingerprints['cookies']:
                    for cookie_name in response.cookies:
                        if cookie_pattern.lower() in cookie_name.lower():
                            cms_matches[cms] += 1
                            cms_evidence[cms].append(f'Cookie: {cookie_name}')
                
                # 3. Check meta tags
                for meta_tag in fingerprints['meta_tags']:
                    for tag in soup.find_all('meta'):
                        if tag.get('name') and tag.get('name').lower() == meta_tag['name'].lower() and tag.get('content'):
                            content = tag.get('content')
                            if re.search(meta_tag['content_regex'], content, re.I):
                                cms_matches[cms] += 2  # Higher confidence for meta generator
                                cms_evidence[cms].append(f'Meta tag {meta_tag["name"]}: {content}')
                                
                                # Extract version from meta tag if available
                                version_match = re.search(meta_tag['content_regex'], content, re.I)
                                if version_match and len(version_match.groups()) > 0 and version_match.group(1):
                                    results['version'] = version_match.group(1)
                                    results['version_confidence'] = 80
                
                # 4. Check for CMS-specific paths
                if deep_scan:
                    for path in fingerprints['paths']:
                        full_url = urljoin(url, path)
                        try:
                            path_response = await client.head(full_url, headers=headers)
                            if path_response.status_code < 400:  # Path exists
                                cms_matches[cms] += 1
                                cms_evidence[cms].append(f'Path exists: {path}')
                        except Exception as e:
                            logger.debug(f"Error checking path {full_url}: {str(e)}")
                
                # 5. Check regex patterns in HTML
                for pattern in fingerprints['regex_patterns']:
                    if re.search(pattern, response.text, re.I):
                        cms_matches[cms] += 1
                        cms_evidence[cms].append(f'Pattern match: {pattern}')
            
            # Find the CMS with the most matches
            best_cms = None
            best_score = 0
            
            for cms, score in cms_matches.items():
                if score > best_score:
                    best_cms = cms
                    best_score = score
            
            # Only consider it detected if we have enough evidence
            if best_cms and best_score >= 2:
                results['detected_cms'] = best_cms
                results['evidence'] = cms_evidence[best_cms]
                
                # Calculate confidence level based on number of matches
                if best_score >= 5:
                    results['confidence'] = 90
                elif best_score >= 3:
                    results['confidence'] = 70
                else:
                    results['confidence'] = 40
                
                # If we detected a CMS and deep_scan is enabled, look for version info
                if deep_scan and results['version'] is None:
                    version_info = await _detect_cms_version(client, url, best_cms)
                    if version_info['version']:
                        results['version'] = version_info['version']
                        results['version_confidence'] = version_info['confidence']
                        results['evidence'].extend(version_info['evidence'])
                
                # Look for plugins and themes based on CMS
                if deep_scan and best_cms == 'WordPress':
                    plugins_themes = await _detect_wordpress_plugins_themes(client, url, soup)
                    results['detected_plugins'] = plugins_themes['plugins']
                    results['detected_themes'] = plugins_themes['themes']
                
                # Get additional info based on CMS
                results['additional_info'] = await _get_cms_additional_info(best_cms, results['version'])
    
    except Exception as e:
        logger.error(f"Error in CMS detection: {str(e)}")
        results['error'] = str(e)
    
    return results

async def _detect_cms_version(client: httpx.AsyncClient, url: str, cms_name: str) -> Dict[str, Any]:
    """Attempt to detect the version of the CMS"""
    result = {
        'version': None,
        'confidence': 0,
        'evidence': []
    }
    
    # Skip if CMS not found in fingerprints
    if cms_name not in CMS_FINGERPRINTS:
        return result
    
    # Get version detection paths for the CMS
    version_paths = CMS_FINGERPRINTS[cms_name]['version_paths']
    
    # Try each path to find version information
    for version_path in version_paths:
        try:
            full_url = urljoin(url, version_path['path'])
            response = await client.get(full_url, follow_redirects=True)
            
            if response.status_code == 200:
                # Look for version information in the response
                version_match = re.search(version_path['regex'], response.text, re.I)
                if version_match and len(version_match.groups()) > 0:
                    result['version'] = version_match.group(1)
                    result['confidence'] = 80
                    result['evidence'].append(f'Version from {version_path["path"]}: {result["version"]}')
                    break  # Found version, no need to check further
        except Exception as e:
            logger.debug(f"Error checking version at {version_path['path']}: {str(e)}")
    
    return result

async def _detect_wordpress_plugins_themes(client: httpx.AsyncClient, url: str, soup: BeautifulSoup) -> Dict[str, List[Dict[str, str]]]:
    """Detect WordPress plugins and themes"""
    result = {
        'plugins': [],
        'themes': []
    }
    
    # Look for plugin patterns in HTML
    plugin_patterns = [
        r'\/wp-content\/plugins\/([^\/]+)\/',
        r'plugins_url\(\s*[\'"]([^"\']+)',
    ]
    
    theme_patterns = [
        r'\/wp-content\/themes\/([^\/]+)\/',
        r'get_template_directory_uri\(\s*\).+?([^\/]+)',
    ]
    
    # Check for plugins
    for pattern in plugin_patterns:
        for match in re.finditer(pattern, str(soup), re.I):
            if match and match.group(1) and match.group(1) not in ['plugins', 'js', 'css', 'images', 'img']:
                plugin_name = match.group(1)
                # Check if already in list
                if not any(p['name'] == plugin_name for p in result['plugins']):
                    result['plugins'].append({
                        'name': plugin_name,
                        'path': f'/wp-content/plugins/{plugin_name}/'
                    })
    
    # Check for themes
    for pattern in theme_patterns:
        for match in re.finditer(pattern, str(soup), re.I):
            if match and match.group(1) and match.group(1) not in ['themes', 'js', 'css', 'images', 'img']:
                theme_name = match.group(1)
                # Check if already in list
                if not any(t['name'] == theme_name for t in result['themes']):
                    result['themes'].append({
                        'name': theme_name,
                        'path': f'/wp-content/themes/{theme_name}/'
                    })
    
    return result

async def _get_cms_additional_info(cms_name: str, version: Optional[str]) -> Dict[str, Any]:
    """Get additional information about the CMS"""
    result = {}
    
    if cms_name == 'WordPress':
        result['website'] = 'https://wordpress.org/'
        result['documentation'] = 'https://wordpress.org/documentation/'
        result['is_open_source'] = True
        result['category'] = 'CMS'
        
        if version:
            result['release_date'] = None  # Would need a database of release dates
            result['latest_version'] = None  # Would need to query WP API for this
            result['is_outdated'] = None  # Can't determine without latest version
    
    elif cms_name == 'Drupal':
        result['website'] = 'https://www.drupal.org/'
        result['documentation'] = 'https://www.drupal.org/documentation'
        result['is_open_source'] = True
        result['category'] = 'CMS'
    
    elif cms_name == 'Joomla':
        result['website'] = 'https://www.joomla.org/'
        result['documentation'] = 'https://docs.joomla.org/'
        result['is_open_source'] = True
        result['category'] = 'CMS'
    
    elif cms_name == 'Magento':
        result['website'] = 'https://magento.com/'
        result['documentation'] = 'https://docs.magento.com/'
        result['is_open_source'] = True
        result['category'] = 'E-commerce'
    
    elif cms_name == 'Shopify':
        result['website'] = 'https://www.shopify.com/'
        result['documentation'] = 'https://help.shopify.com/'
        result['is_open_source'] = False
        result['category'] = 'E-commerce'
    
    # Add common security concerns based on CMS
    result['common_security_issues'] = _get_cms_security_issues(cms_name)
    
    return result

def _get_cms_security_issues(cms_name: str) -> List[str]:
    """Get common security issues for a specific CMS"""
    common_issues = {
        'WordPress': [
            'Vulnerable plugins and themes',
            'Outdated WordPress core',
            'Weak admin credentials',
            'XML-RPC enabled',
            'Exposed wp-config.php file',
            'Directory listing enabled',
            'User enumeration',
        ],
        'Drupal': [
            'Outdated Drupal core',
            'Critical Drupalgeddon vulnerabilities',
            'Unsafe contributed modules',
            'PHP filter module enabled',
            'Exposed settings.php file',
        ],
        'Joomla': [
            'Outdated Joomla core',
            'Vulnerable extensions',
            'Directory listing enabled',
            'Default admin user',
            'Configuration.php exposed',
        ],
        'Magento': [
            'Outdated Magento installation',
            'Vulnerable extensions',
            'Admin panel exposure',
            'Missing security patches',
            'Default credentials',
        ],
        'Shopify': [
            'Third-party app vulnerabilities',
            'Custom code issues',
            'Theme vulnerabilities',
        ],
    }
    
    # Return issues for the specific CMS or a generic list
    return common_issues.get(cms_name, [
        'Outdated CMS version',
        'Weak admin credentials',
        'Vulnerable plugins/extensions',
        'Missing security patches',
    ])

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_cms_detector():
        results = await detect_cms("wordpress.org", deep_scan=True)
        print(json.dumps(results, indent=2))
    
    asyncio.run(test_cms_detector()) 