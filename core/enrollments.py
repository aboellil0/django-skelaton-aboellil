from django.db import models
import uuid

class Status(models.TextChoices): 
    """Enumeration for enrollment status choices."""

    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    DROPPED = 'dropped', 'Dropped'
    SUSPENDED = 'suspended', 'Suspended'


class Enrollment(models.Model):
    """Model representing an enrollment of a student or child in a course."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    """make PROTECT to don't risks losing critical data (payment or attendance records linked to enrollments)
       مؤقتا لحد ما نعرف cascade or null
    """
    course = models.ForeignKey('courses.Course', on_delete=models.PROTECT) 
    student = models.ForeignKey('student_users.StudentUser', null=True, blank=True, on_delete=models.PROTECT) 
    child = models.ForeignKey('children.Child', null=True, blank=True, on_delete=models.PROTECT) 
    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT) # connected to admin who approved the enrollment

    enrolled_at = models.DateTimeField() # date time when he wanted to enroll from pending enrollment to active enrollment
    active = models.BooleanField(default=True) # default active because when admin approves the pending enrollment it becomes active
    status = models.CharField(max_length=10, choices=Status.choices, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        """meta class for Enrollment model."""
        
        """"Ensure either child or student is set, but not both or neither."""
        constraints = [
            models.CheckConstraint(
                check=
                models.Q(child__isnull=False, student__isnull=True) | 
                models.Q(child__isnull=True, student__isnull=False),
                name='one_child_or_student'
            ),
            models.UniqueConstraint(fields=['course', 'child'], name='unique_course_child'), 
            models.UniqueConstraint(fields=['course', 'student'], name='unique_course_student'),
        ]

        indexes = [
            models.Index(fields=['course'], name='course_index'),
            models.Index(fields=['student'], name='student_index'),
            models.Index(fields=['child'], name='child_index'),
        ]
    
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
 


    def update_status(self, new_status):
        """Update the enrollment status with validation and related actions"""
        from django.core.exceptions import ValidationError

        allowed_transitions = {
            Status.ACTIVE: [Status.COMPLETED, Status.DROPPED, Status.SUSPENDED],
            Status.COMPLETED: [],
            Status.DROPPED: [],
            Status.SUSPENDED: [Status.ACTIVE],
        }

        if new_status not in Status.values:
            raise ValidationError(f"Invalid status: {new_status}")

        if new_status not in allowed_transitions[self.status]:
            raise ValidationError(f"Cannot transition from {self.status} to {new_status}")

        self.status = new_status
        self.active = new_status == Status.ACTIVE
        self.save()
            
    def clean(self):
        """Ensure either child or student is set, but not both or neither."""
        from django.core.exceptions import ValidationError

        if (self.child is None and self.student is None) or (self.child is not None and self.student is not None):
            raise ValidationError("Select exactly one of student or child.")
        
    def __str__(self):
        """String representation of the Enrollment."""
        participant = self.student if self.student else self.child or 'Unknown'
        return f"Enrollment for {participant} in {self.course}"
    
