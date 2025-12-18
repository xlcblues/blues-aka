import logging
from flask import Blueprint, request
from blues_aka.common.responseapi import handle_api_response
from blues_aka.user.schemas import userRoleQuerySchema

logger = logging.getLogger(__name__)
role_bp = Blueprint('role', __name__, url_prefix='/role')

# 管理员查询用户角色
# @role_bp.route('/role', methods=['GET'])
# @handle_api_response
# def get_role():
#     try:
#         query_data = userRoleQuerySchema().load(request.args)
#
#         username = query_data['username']
#         role = query_data['role']
#
#

