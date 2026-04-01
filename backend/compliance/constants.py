"""
UK Tax Constants — Tax Year 2025/26

These are the official HMRC rates and thresholds used by the
Compliance Engine for gross-to-net calculations, RTI submissions,
and pre-payroll validation.

Source: HMRC Tax Year 2025-26 parameters.
These MUST be updated at the start of each new tax year.
"""

# =============================================================================
# INCOME TAX BANDS (2025/26)
# =============================================================================

PERSONAL_ALLOWANCE = 12570  # Annual tax-free allowance
PERSONAL_ALLOWANCE_TAPER_THRESHOLD = 100000  # PA reduces above this

# Tax bands (annual thresholds)
TAX_BANDS = [
    {
        'name': 'Personal Allowance',
        'lower': 0,
        'upper': 12570,
        'rate': 0.00,
    },
    {
        'name': 'Basic Rate',
        'lower': 12570,
        'upper': 50270,
        'rate': 0.20,
    },
    {
        'name': 'Higher Rate',
        'lower': 50270,
        'upper': 125140,
        'rate': 0.40,
    },
    {
        'name': 'Additional Rate',
        'lower': 125140,
        'upper': float('inf'),
        'rate': 0.45,
    },
]


# =============================================================================
# NATIONAL INSURANCE CONTRIBUTIONS (2025/26)
# =============================================================================

# Employee NI (Class 1 Primary)
EMPLOYEE_NI = {
    'primary_threshold_annual': 12570,  # Below this: no NI
    'upper_earnings_limit_annual': 50270,  # Above this: lower NI rate
    'main_rate': 0.08,  # Between PT and UEL
    'additional_rate': 0.02,  # Above UEL
}

# Employer NI (Class 1 Secondary)
EMPLOYER_NI = {
    'secondary_threshold_annual': 5000,  # Employer NI starts above this
    'rate': 0.15,
    'employment_allowance': 10500,  # Annual employer NI allowance
}


# =============================================================================
# STUDENT LOAN REPAYMENT THRESHOLDS (2025/26)
# =============================================================================

STUDENT_LOAN_PLANS = {
    'plan_1': {
        'threshold_annual': 24990,
        'rate': 0.09,
    },
    'plan_2': {
        'threshold_annual': 27295,
        'rate': 0.09,
    },
    'plan_4': {  # Scotland
        'threshold_annual': 27660,
        'rate': 0.09,
    },
    'plan_5': {
        'threshold_annual': 25000,
        'rate': 0.09,
    },
    'postgraduate': {
        'threshold_annual': 21000,
        'rate': 0.06,
    },
}


# =============================================================================
# PENSION AUTO-ENROLMENT (2025/26)
# =============================================================================

PENSION = {
    'lower_earnings_threshold': 6240,  # Annual
    'upper_earnings_threshold': 50270,  # Annual (same as UEL)
    'employee_rate': 0.05,  # Minimum 5%
    'employer_rate': 0.03,  # Minimum 3%
}


# =============================================================================
# TAX CODE PATTERNS
# =============================================================================

# Common tax code patterns for validation
EMERGENCY_TAX_CODES = ['1257L', '1257L W1', '1257L M1', '1257L X']
STANDARD_TAX_CODE = '1257L'

# Tax code format: numbers followed by a letter suffix
# e.g., 1257L, 1100L, BR, D0, D1, NT, 0T
VALID_TAX_CODE_SUFFIXES = ['L', 'M', 'N', 'T', 'BR', 'D0', 'D1', 'NT', '0T', 'K']


# =============================================================================
# NI NUMBER VALIDATION
# =============================================================================

NI_NUMBER_REGEX = r'^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$'
# First 2 chars: letters (excluding D, F, I, Q, U, V)
# Next 6 chars: digits
# Last char: A, B, C, or D


# =============================================================================
# HMRC RTI SUBMISSION
# =============================================================================

HMRC_RTI = {
    'fps_deadline_days': 0,  # FPS must be submitted on or before payday
    'eps_deadline_day': 19,  # EPS due by 19th of following month
    'max_retries': 3,
    'retry_delay_seconds': 300,  # 5 minutes between retries
}


# =============================================================================
# COMPLIANCE DOCUMENT RETENTION
# =============================================================================

DOCUMENT_RETENTION_YEARS = 7  # Statutory minimum retention period


# =============================================================================
# ANOMALY DETECTION THRESHOLDS
# =============================================================================

ANOMALY_THRESHOLDS = {
    'gross_pay_variance_pct': 50,  # Flag if gross pay differs by >50% from average
    'max_weekly_hours': 60,  # Flag if declared hours exceed this
    'min_hourly_rate': 11.44,  # National Living Wage 2025/26 (21+)
}
