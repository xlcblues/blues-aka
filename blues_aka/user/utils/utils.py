from flask import request
import requests

def get_client_ip():
    """获取客户端真实IP地址"""
    # 检查X-Forwarded-For头（反向代理设置）
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    # 检查X-Real-IP头（Nginx常用）
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    # 默认使用远程地址
    else:
        ip = request.remote_addr

    # 处理IPv6映射的IPv4地址
    if ip.startswith('::ffff:'):
        ip = ip.split(':')[-1]

    return ip

def get_ip_location(ip):
    """获取IP地址的地理位置信息"""
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone"
        response = requests.get(url, timeout=3)
        data = response.json()

        if data.get('status') == 'success':
            return {
                'ip': ip,
                'country': data.get('country'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'postal': data.get('zip'),
                'latitude': data.get('lat'),
                'longitude': data.get('lon'),
                'timezone': data.get('timezone')
            }
        else:
            return {'error': data.get('message', 'Location lookup failed')}

    except Exception as e:
        return {'error': f'Request failed: {str(e)}'}

