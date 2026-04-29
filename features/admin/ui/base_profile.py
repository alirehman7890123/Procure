from PySide6.QtWidgets import QStackedLayout

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseProfileWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.changepassword_widget = None
        self.profile_widget = None
        self.userlist_widget = None
        self.userdetail_widget = None
        self.adduser_widget = None

        self.setLayout(self.stacked_layout)

    def _ensure_changepassword_widget(self):
        if self.changepassword_widget is None:
            from medic.features.admin.ui.change_password import ChangePasswordWidget

            self.changepassword_widget = ChangePasswordWidget()
            self.changepassword_widget.profilebutton.clicked.connect(self.set_profile_widget)
            self.stacked_layout.addWidget(self.changepassword_widget)
        return self.changepassword_widget

    def _ensure_profile_widget(self):
        if self.profile_widget is None:
            from medic.features.admin.ui.profile import ProfileWidget

            self.profile_widget = ProfileWidget()
            self.profile_widget.userlist.clicked.connect(self.set_userlist_widget)
            self.profile_widget.changepassword.clicked.connect(self.set_changepassword_widget)
            self.stacked_layout.addWidget(self.profile_widget)
        return self.profile_widget

    def _ensure_userlist_widget(self):
        if self.userlist_widget is None:
            from medic.features.admin.ui.users_list import UserListWidget

            self.userlist_widget = UserListWidget()
            self.userlist_widget.adduser.clicked.connect(self.set_adduser_widget)
            self.userlist_widget.detailpagesignal.connect(self.set_userdetail_widget)
            self.stacked_layout.addWidget(self.userlist_widget)
        return self.userlist_widget

    def _ensure_userdetail_widget(self):
        if self.userdetail_widget is None:
            from medic.features.admin.ui.user_detail import UserDetailWidget

            self.userdetail_widget = UserDetailWidget()
            self.userdetail_widget.userlist.clicked.connect(self.set_userlist_widget)
            self.stacked_layout.addWidget(self.userdetail_widget)
        return self.userdetail_widget

    def _ensure_adduser_widget(self):
        if self.adduser_widget is None:
            from medic.features.admin.ui.add_user import AddUserWidget

            self.adduser_widget = AddUserWidget()
            self.adduser_widget.userlist.clicked.connect(self.set_userlist_widget)
            self.stacked_layout.addWidget(self.adduser_widget)
        return self.adduser_widget

    @Permissions.require_permission("profile.update")
    def set_changepassword_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_changepassword_widget())

    @Permissions.require_permission("profile.view")
    def set_profile_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_profile_widget())

    @Permissions.require_permission("users.view")
    def set_userlist_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_userlist_widget())

    @Permissions.require_permission("users.view")
    def set_userdetail_widget(self, user_id):
        self._ensure_userdetail_widget()
        self.userdetail_widget.load_user_data(user_id)
        self.stacked_layout.setCurrentWidget(self.userdetail_widget)

    @Permissions.require_permission("users.create")
    def set_adduser_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_adduser_widget())

    def reset_to_default(self):
        if Permissions.has_permission("profile.view"):
            self.stacked_layout.setCurrentWidget(self._ensure_profile_widget())
        elif Permissions.has_permission("users.view"):
            self.stacked_layout.setCurrentWidget(self._ensure_userlist_widget())
        elif Permissions.has_permission("profile.update"):
            self.stacked_layout.setCurrentWidget(self._ensure_changepassword_widget())
        elif Permissions.has_permission("users.create"):
            self.stacked_layout.setCurrentWidget(self._ensure_adduser_widget())
