from PySide6.QtWidgets import QWidget, QStackedLayout

from userprofile.changepassword import ChangePasswordWidget
from userprofile.userprofile import ProfileWidget
from userprofile.userslist import UserListWidget
from userprofile.userdetail import UserDetailWidget
from userprofile.adduser import AddUserWidget
from utilities.basepage import BasePage
from utilities.permissions import Permissions

class Profile:
        
    def __init__(self, id, firstname, lastname, email, username, password, salt, role, status, creation, parent=None):

        super().__init__(parent)

        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.username = username
        self.password = password
        self.salt = salt
        self.role = role
        self.status = status
        self.creation = creation




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


    @Permissions.require_permission('profile.update')
    def set_changepassword_widget(self):
        self.stacked_layout.setCurrentWidget(self.changepassword_widget)
        
    @Permissions.require_permission('profile.view')
    def set_profile_widget(self):
        self.stacked_layout.setCurrentWidget(self.profile_widget)
        
    @Permissions.require_permission('users.view')
    def set_userlist_widget(self):
        self.stacked_layout.setCurrentWidget(self.userlist_widget)

    @Permissions.require_permission('users.view')
    def set_userdetail_widget(self, user_id):
        self.userdetail_widget.load_user_data(user_id)
        self.stacked_layout.setCurrentWidget(self.userdetail_widget)

    @Permissions.require_permission('users.create')
    def set_adduser_widget(self):
        self.stacked_layout.setCurrentWidget(self.adduser_widget)


    # 🔑 reset method
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.profile_widget)






