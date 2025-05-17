# from .basic_recon import run_basic_recon
from .standard_recon_workflow import run_standard_recon_workflow
from .targeted_recon_workflow import run_targeted_recon_workflow
from .stealth_recon_workflow import run_stealth_recon_workflow
from .comprehensive_recon_workflow import run_comprehensive_recon_workflow

# Define workflow types for main.py
WORKFLOW_TYPES = {
    "standard": run_standard_recon_workflow,
    "quick": run_standard_recon_workflow,  # Quick is implemented within standard with different params
    "deep": run_standard_recon_workflow,   # Deep is implemented within standard with different params
    "targeted": run_targeted_recon_workflow,
    "stealth": run_stealth_recon_workflow,
    "comprehensive": run_comprehensive_recon_workflow
}