from PySide6.QtWidgets import QStackedLayout

from features.admin.ui.add_user import AddUserWidget
from features.admin.ui.change_password import ChangePasswordWidget
from features.admin.ui.profile import ProfileWidget
from features.admin.ui.user_detail import UserDetailWidget
from features.admin.ui.users_list import UserListWidget
from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseProfileWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()

        self.changepassword_widget = ChangePasswordWidget()
        self.changepassword_widget.profilebutton.clicked.connect(self.set_profile_widget)

        self.profile_widget = ProfileWidget()
        self.profile_widget.userlist.clicked.connect(self.set_userlist_widget)
        self.profile_widget.changepassword.clicked.connect(self.set_changepassword_widget)

        self.userlist_widget = UserListWidget()
        self.userlist_widget.adduser.clicked.connect(self.set_adduser_widget)
        self.userlist_widget.detailpagesignal.connect(self.set_userdetail_widget)

        self.userdetail_widget = UserDetailWidget()
        self.userdetail_widget.userlist.clicked.connect(self.set_userlist_widget)

        self.adduser_widget = AddUserWidget()
        self.adduser_widget.userlist.clicked.connect(self.set_userlist_widget)

        self.stacked_layout.addWidget(self.changepassword_widget)
        self.stacked_layout.addWidget(self.profile_widget)
        self.stacked_layout.addWidget(self.userlist_widget)
        self.stacked_layout.addWidget(self.userdetail_widget)
        self.stacked_layout.addWidget(self.adduser_widget)

        self.setLayout(self.stacked_layout)

    @Permissions.require_permission("profile.update")
    def set_changepassword_widget(self):
        self.stacked_layout.setCurrentWidget(self.changepassword_widget)

    @Permissions.require_permission("profile.view")
    def set_profile_widget(self):
        self.stacked_layout.setCurrentWidget(self.profile_widget)

    @Permissions.require_permission("users.view")
    def set_userlist_widget(self):
        self.stacked_layout.setCurrentWidget(self.userlist_widget)

    @Permissions.require_permission("users.view")
    def set_userdetail_widget(self, user_id):
        self.userdetail_widget.load_user_data(user_id)
        self.stacked_layout.setCurrentWidget(self.userdetail_widget)

    @Permissions.require_permission("users.create")
    def set_adduser_widget(self):
        self.stacked_layout.setCurrentWidget(self.adduser_widget)

    def reset_to_default(self):
        if Permissions.has_permission("profile.view"):
            self.stacked_layout.setCurrentWidget(self.profile_widget)
        elif Permissions.has_permission("users.view"):
            self.stacked_layout.setCurrentWidget(self.userlist_widget)
        elif Permissions.has_permission("profile.update"):
            self.stacked_layout.setCurrentWidget(self.changepassword_widget)
        elif Permissions.has_permission("users.create"):
            self.stacked_layout.setCurrentWidget(self.adduser_widget)
