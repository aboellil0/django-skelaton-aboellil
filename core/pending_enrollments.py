from datetime import timezone
from django.db import models
import uuid

from django.forms import ValidationError

class Status(models.TextChoices):
    """Enumeration for pending enrollment status choices."""
    PENDING = 'pending', 'Pending'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'
    ACCEPTED = 'accepted', 'Accepted'

class PendingEnrollment(models.Model):
    """Model representing a pending enrollment request for a course."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    """make PROTECT to don't risks losing critical data (payment or attendance records linked to enrollments)
       مؤقتا لحد ما نعرف cascade or null
    """
    course = models.ForeignKey('courses.Course', on_delete=models.PROTECT, related_name='pending_enrollments')
    parent = models.ForeignKey('parents.Parent', null=True, blank=True, on_delete=models.PROTECT, related_name='pending_enrollments')
    student = models.ForeignKey('student_users.StudentUser', null=True, blank=True, on_delete=models.PROTECT, related_name='pending_enrollments')
    child = models.ForeignKey('children.Child', null=True, blank=True, on_delete=models.PROTECT, related_name='pending_enrollments')
    
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    processed_by = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.PROTECT, related_name='processed_pending_enrollments')
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class for PendingEnrollment model."""
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(parent__isnull=False, child__isnull=False, student__isnull=True) |
                    models.Q(student__isnull=False, parent__isnull=True, child__isnull=True)
                ),
                name='parent_child_or_student'
            ),
        ]
        indexes = [
            models.Index(fields=['course'], name='pending_course_index'),
            models.Index(fields=['parent'], name='pending_parent_index'),
            models.Index(fields=['student'], name='pending_student_index'),
            models.Index(fields=['status'], name='pending_status_index'),
            models.Index(fields=['expires_at'], name='pending_expires_index'),
        ]
        verbose_name = 'Pending Enrollment'
        verbose_name_plural = 'Pending Enrollments'

    def clean(self):
        """Ensure parent and child are set together or student is set alone."""
        if (self.parent is not None and self.child is not None and self.student is None) or \
           (self.student is not None and self.parent is None and self.child is None):
            pass  # Valid cases
        else:
            raise ValidationError("Select either a parent and child together or a student alone.")

    def update_status(self, new_status, processed_by=None):
        """Update the pending enrollment status with validation."""
        allowed_transitions = {
            Status.PENDING: [Status.ACCEPTED, Status.CANCELLED, Status.EXPIRED],
            Status.ACCEPTED: [],
            Status.CANCELLED: [],
            Status.EXPIRED: [],
        }

        if new_status not in Status.values:
            raise ValidationError(f"Invalid status: {new_status}")
        if new_status not in allowed_transitions[self.status]:
            raise ValidationError(f"Cannot transition from {self.status} to {new_status}")

        self.status = new_status
        if new_status in [Status.ACCEPTED, Status.CANCELLED]:
            self.processed_at = timezone.now()
            self.processed_by = processed_by
        self.save()

    def expire(self):
        """Mark the pending enrollment as expired if past expires_at"""
        if self.status != Status.PENDING:
            raise ValidationError("Only pending enrollments can be expired.")
        if self.expires_at and self.expires_at <= timezone.now():
            self.status = Status.EXPIRED
            self.processed_at = timezone.now()
            self.save()

    def to_enrollment(self):
        """Convert to an Enrollment record upon acceptance"""
        from .enrollments import Enrollment  # Adjust import based on your structure

        if self.status != Status.ACCEPTED:
            raise ValidationError("Only accepted pending enrollments can be converted to enrollments.")

        enrollment = Enrollment(
            course=self.course,
            student=self.student,
            child=self.child,
            enrolled_at=self.processed_at,
            created_by=self.processed_by,
            status='active',
            active=True,
        )
        enrollment.full_clean()
        enrollment.save()
        return enrollment

    def __str__(self):
        """String representation of the PendingEnrollment"""
        participant = self.student if self.student else self.child or 'Unknown'
        return f"Pending Enrollment for {participant} in {self.course}"