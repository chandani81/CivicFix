from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager since we log in with email, not username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", User.Role.CITIZEN)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    CivicFix user.

    role = citizen    -> registers themselves, submits and tracks complaints
    role = department -> registers themselves and picks their department,
                          manages complaints routed to that department
    role = admin      -> full access; created only via the admin panel
                          (not self-registerable), manages users/departments
    """

    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        DEPARTMENT = "department", "Department Staff"
        ADMIN = "admin", "Admin"

    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CITIZEN)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_members",
        help_text="Set only when role='department'",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_citizen(self):
        return self.role == self.Role.CITIZEN

    @property
    def is_department_staff(self):
        return self.role == self.Role.DEPARTMENT

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser
