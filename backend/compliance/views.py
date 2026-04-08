from django.http import JsonResponse
from compliance.models import ComplianceCheck, RTISubmission
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def users_list(request):
    users = list(User.objects.values('id', 'username', 'email'))
    return JsonResponse(users, safe=False)
def dashboard_data(request):
    audit_total = ComplianceCheck.objects.count()

    exceptions_active = ComplianceCheck.objects.filter(all_passed=False).count()

    total = ComplianceCheck.objects.count()
    passed = ComplianceCheck.objects.filter(all_passed=True).count()

    compliance_passed = int((passed / total) * 100) if total > 0 else 0

    rti_pending = RTISubmission.objects.filter(status="PENDING").count()

    return JsonResponse({
        "audit_total": audit_total,
        "exceptions_active": exceptions_active,
        "compliance_passed": compliance_passed,
        "rti_pending": rti_pending
    })