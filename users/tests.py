from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings

from .models import PasswordSetupToken, User
from .services import UserService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_admin(**kwargs) -> User:
    kwargs.setdefault("email", "admin@test.com")
    kwargs.setdefault("role", User.Role.ADMIN)
    kwargs.setdefault("must_change_password", False)
    return User.objects.create_user(**kwargs)


def make_writer(**kwargs) -> User:
    kwargs.setdefault("email", "writer@test.com")
    kwargs.setdefault("role", User.Role.WRITER)
    return User.objects.create_user(**kwargs)


def make_reviewer(**kwargs) -> User:
    kwargs.setdefault("email", "reviewer@test.com")
    kwargs.setdefault("role", User.Role.REVIEWER)
    return User.objects.create_user(**kwargs)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class UserModelTest(TestCase):
    def test_email_is_unique_identifier(self):
        user = User.objects.create_user(email="unique@test.com", role=User.Role.WRITER)
        self.assertEqual(user.USERNAME_FIELD, "email")

    def test_username_auto_derived_from_email(self):
        user = User.objects.create_user(email="firstname@test.com", role=User.Role.WRITER)
        self.assertEqual(user.username, "firstname")

    def test_username_collision_resolved(self):
        User.objects.create_user(email="jo@test.com", role=User.Role.WRITER)
        user2 = User.objects.create_user(email="jo@other.com", role=User.Role.WRITER)
        self.assertEqual(user2.username, "jo1")

    def test_must_change_password_default_true(self):
        user = User.objects.create_user(email="new@test.com", role=User.Role.WRITER)
        self.assertTrue(user.must_change_password)

    def test_new_user_has_unusable_password(self):
        user = User.objects.create_user(email="nopw@test.com", role=User.Role.WRITER)
        self.assertFalse(user.has_usable_password())

    def test_str_representation(self):
        user = User.objects.create_user(email="repr@test.com", role=User.Role.ADMIN)
        self.assertIn("repr@test.com", str(user))
        self.assertIn("admin", str(user))


# ---------------------------------------------------------------------------
# Role helper tests
# ---------------------------------------------------------------------------

class RoleHelperTest(TestCase):
    def setUp(self):
        self.writer = make_writer()
        self.reviewer = make_reviewer()
        self.admin = make_admin()

    def test_is_writer(self):
        self.assertTrue(self.writer.is_writer())
        self.assertFalse(self.writer.is_reviewer())
        self.assertFalse(self.writer.is_admin())

    def test_is_reviewer(self):
        self.assertTrue(self.reviewer.is_reviewer())
        self.assertFalse(self.reviewer.is_writer())
        self.assertFalse(self.reviewer.is_admin())

    def test_is_admin(self):
        self.assertTrue(self.admin.is_admin())
        self.assertFalse(self.admin.is_writer())
        self.assertFalse(self.admin.is_reviewer())


# ---------------------------------------------------------------------------
# UserService.create_user tests
# ---------------------------------------------------------------------------

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class UserServiceCreateTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.writer = make_writer()

    def test_admin_can_create_writer(self):
        user = UserService.create_user(
            acting_user=self.admin,
            email="newwriter@test.com",
            role=User.Role.WRITER,
            send_email=False,
        )
        self.assertEqual(user.role, User.Role.WRITER)
        self.assertTrue(user.must_change_password)

    def test_admin_can_create_reviewer(self):
        user = UserService.create_user(
            acting_user=self.admin,
            email="newreviewer@test.com",
            role=User.Role.REVIEWER,
            send_email=False,
        )
        self.assertEqual(user.role, User.Role.REVIEWER)

    def test_admin_can_create_admin(self):
        user = UserService.create_user(
            acting_user=self.admin,
            email="newadmin@test.com",
            role=User.Role.ADMIN,
            send_email=False,
        )
        self.assertEqual(user.role, User.Role.ADMIN)

    def test_non_admin_cannot_create_user(self):
        with self.assertRaises(PermissionDenied):
            UserService.create_user(
                acting_user=self.writer,
                email="another@test.com",
                role=User.Role.WRITER,
                send_email=False,
            )

    def test_invalid_role_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            UserService.create_user(
                acting_user=self.admin,
                email="bad@test.com",
                role="supervillain",
                send_email=False,
            )

    def test_token_created_on_user_creation(self):
        user = UserService.create_user(
            acting_user=self.admin,
            email="tokentest@test.com",
            role=User.Role.WRITER,
            send_email=False,
        )
        self.assertTrue(PasswordSetupToken.objects.filter(user=user, is_used=False).exists())

    def test_email_sent_on_creation(self):
        UserService.create_user(
            acting_user=self.admin,
            email="emailtest@test.com",
            role=User.Role.WRITER,
            send_email=True,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("emailtest@test.com", mail.outbox[0].to)
        self.assertIn("Set up your Ethiopian Daily account password", mail.outbox[0].subject)

    def test_email_contains_token_link(self):
        user = UserService.create_user(
            acting_user=self.admin,
            email="linktest@test.com",
            role=User.Role.WRITER,
            send_email=True,
        )
        token = PasswordSetupToken.objects.get(user=user)
        self.assertIn(token.token, mail.outbox[0].body)


# ---------------------------------------------------------------------------
# Password setup workflow tests
# ---------------------------------------------------------------------------

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordSetupWorkflowTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.new_user = UserService.create_user(
            acting_user=self.admin,
            email="setup@test.com",
            role=User.Role.WRITER,
            send_email=False,
        )
        self.token_obj = PasswordSetupToken.objects.get(user=self.new_user)

    def test_valid_token_sets_password(self):
        user = UserService.setup_password(
            token_str=self.token_obj.token,
            new_password="SecurePass@123",
        )
        self.assertTrue(user.check_password("SecurePass@123"))

    def test_must_change_password_cleared_after_setup(self):
        user = UserService.setup_password(
            token_str=self.token_obj.token,
            new_password="SecurePass@123",
        )
        self.assertFalse(user.must_change_password)

    def test_token_marked_used_after_setup(self):
        UserService.setup_password(
            token_str=self.token_obj.token,
            new_password="SecurePass@123",
        )
        self.token_obj.refresh_from_db()
        self.assertTrue(self.token_obj.is_used)

    def test_used_token_cannot_be_reused(self):
        UserService.setup_password(
            token_str=self.token_obj.token,
            new_password="SecurePass@123",
        )
        with self.assertRaises(ValidationError):
            UserService.setup_password(
                token_str=self.token_obj.token,
                new_password="AnotherPass@456",
            )

    def test_invalid_token_raises_error(self):
        with self.assertRaises(ValidationError):
            UserService.setup_password(
                token_str="totally-fake-token",
                new_password="SecurePass@123",
            )

    def test_weak_password_rejected(self):
        # Django's validators should reject a password that is too common/short.
        with self.assertRaises(ValidationError):
            UserService.setup_password(
                token_str=self.token_obj.token,
                new_password="password",
            )


# ---------------------------------------------------------------------------
# Role-based permission enforcement tests
# ---------------------------------------------------------------------------

class RolePermissionEnforcementTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.writer = make_writer()
        self.reviewer = make_reviewer()

    def test_admin_can_manage_users(self):
        # Should not raise.
        UserService.assert_can_manage_users(self.admin)

    def test_writer_cannot_manage_users(self):
        with self.assertRaises(PermissionDenied):
            UserService.assert_can_manage_users(self.writer)

    def test_reviewer_cannot_manage_users(self):
        with self.assertRaises(PermissionDenied):
            UserService.assert_can_manage_users(self.reviewer)

    def test_writer_can_write_articles(self):
        UserService.assert_can_write_articles(self.writer)

    def test_admin_can_write_articles(self):
        UserService.assert_can_write_articles(self.admin)

    def test_reviewer_cannot_write_articles(self):
        with self.assertRaises(PermissionDenied):
            UserService.assert_can_write_articles(self.reviewer)

    def test_reviewer_can_review_articles(self):
        UserService.assert_can_review_articles(self.reviewer)

    def test_admin_can_review_articles(self):
        UserService.assert_can_review_articles(self.admin)

    def test_writer_cannot_review_articles(self):
        with self.assertRaises(PermissionDenied):
            UserService.assert_can_review_articles(self.writer)


# ---------------------------------------------------------------------------
# Resend setup email tests
# ---------------------------------------------------------------------------

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ResendSetupEmailTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.new_user = UserService.create_user(
            acting_user=self.admin,
            email="resend@test.com",
            role=User.Role.WRITER,
            send_email=False,
        )

    def test_resend_creates_new_token(self):
        old_token = PasswordSetupToken.objects.get(user=self.new_user).token
        UserService.resend_setup_email(acting_user=self.admin, target_user=self.new_user)
        new_token = PasswordSetupToken.objects.get(user=self.new_user).token
        self.assertNotEqual(old_token, new_token)

    def test_resend_sends_email(self):
        UserService.resend_setup_email(acting_user=self.admin, target_user=self.new_user)
        self.assertEqual(len(mail.outbox), 1)

    def test_non_admin_cannot_resend(self):
        writer = make_writer(email="writer2@test.com")
        with self.assertRaises(PermissionDenied):
            UserService.resend_setup_email(acting_user=writer, target_user=self.new_user)

    def test_cannot_resend_to_user_who_already_set_password(self):
        token = PasswordSetupToken.objects.get(user=self.new_user).token
        UserService.setup_password(token_str=token, new_password="SecurePass@123")
        with self.assertRaises(ValidationError):
            UserService.resend_setup_email(acting_user=self.admin, target_user=self.new_user)
