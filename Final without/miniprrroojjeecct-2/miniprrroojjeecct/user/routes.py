from flask import Blueprint

from tester import tester
from user.models import User



@tester.route('/user/signup',methods=['GET'])
def signup():
    return User().signup()
