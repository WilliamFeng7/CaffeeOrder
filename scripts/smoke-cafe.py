#!/usr/bin/env python3
"""仅对 dev + mock 环境执行。保留验收订单，恢复营业设置并删除临时员工/商品。"""
import datetime as dt
import io
import json
import os
from pathlib import Path
import secrets
import urllib.error
import urllib.parse
import urllib.request
import zipfile

BASE = os.environ.get('CAFE_API_URL', 'http://127.0.0.1:48080').rstrip('/')
APP_BASE = os.environ.get('CAFE_APP_API_URL', BASE).rstrip('/')
ADMIN_BASE = os.environ.get('CAFE_ADMIN_API_URL', BASE).rstrip('/')
MOCK_INITIAL_BALANCE = int(os.environ.get('CAFE_MOCK_INITIAL_BALANCE_CENTS', '50000'))
DEV_LOGIN_SECRET = os.environ.get('CAFE_DEV_LOGIN_SECRET', '')
RUN = dt.datetime.now(dt.timezone.utc).strftime('%m%d%H%M%S') + secrets.token_hex(3)
checks = 0


def check(condition, message):
    global checks
    if not condition:
        raise AssertionError(message)
    checks += 1
    print('PASS ' + message)


def call(method, path, data=None, token=None, key=None, params=None, success=True, dev_secret=False):
    if params:
        path += '?' + urllib.parse.urlencode(params)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if key:
        headers['Idempotency-Key'] = key
    if dev_secret:
        headers['X-Cafe-Dev-Secret'] = DEV_LOGIN_SECRET
    payload = None if data is None else json.dumps(data, ensure_ascii=False).encode()
    origin = ADMIN_BASE if path.startswith('/admin-api') else APP_BASE
    request = urllib.request.Request(origin + path, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        raw = error.read()
    result = json.loads(raw)
    if success and result.get('code') != 0:
        raise AssertionError(f'{method} {path}: {result.get("code")} {result.get("msg")}')
    return result.get('data') if success else result


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f'缺少环境变量 {name}')
    return value


def admin_login(username, password):
    return call('POST', '/admin-api/system/auth/login', {'username': username, 'password': password})['accessToken']


def app_page(token):
    return call('GET', '/app-api/cafe/order/page', token=token, params={'pageSize': 100})['list']


def run():
    admin = admin_login(
        os.environ.get('CAFE_ADMIN_USERNAME', 'admin'),
        required_env('CAFE_ADMIN_PASSWORD'),
    )
    original_shop = call('GET', '/admin-api/cafe/shop/get', token=admin)
    employees, entities = [], []
    try:
        # 先确认开发接口存在，再修改任何营业配置。
        student_no = 'SMOKE' + RUN
        student = call('POST', '/app-api/cafe/auth/dev-login', {'studentNo': student_no, 'name': '验收学生'}, dev_secret=True)
        student_token = student['accessToken']
        check(isinstance(student['expiresTime'], int), '学生令牌过期时间为毫秒时间戳')
        check(call('GET', '/app-api/cafe/student/me', token=student_token)['balance'] == MOCK_INITIAL_BALANCE,
              f'mock 学生卡初始余额为 {MOCK_INITIAL_BALANCE} 分')
        menu = call('GET', '/app-api/cafe/menu')
        check(len(menu['categories']) >= 4 and len(menu['items']) >= 11, '免登录菜单包含初始分类、11 个商品及规格')
        check(call('GET', '/app-api/cafe/auth/dingtalk-config') is not None, '钉钉 corpId 配置接口免登录')
        check(call('GET', '/app-api/cafe/student/me', success=False)['code'] != 0, '学生私有接口拒绝未登录请求')

        def employee(role, nickname):
            username = 'smk' + str(role) + RUN
            password = 'S' + secrets.token_hex(6)
            user_id = call('POST', '/admin-api/system/user/create', {'username': username, 'password': password, 'nickname': nickname, 'deptId': 1, 'postIds': [], 'sex': 0, 'email': '', 'mobile': '', 'remark': '本地接口验收'}, token=admin)
            employees.append(user_id)
            call('POST', '/admin-api/system/permission/assign-user-role', {'userId': user_id, 'roleIds': [role]}, token=admin)
            return admin_login(username, password)

        manager = employee(2, '验收店长')
        barista = employee(3, '验收咖啡师')
        barista_info = call('GET', '/admin-api/system/auth/get-permission-info', token=barista)
        check(barista_info['menus'] == [], '咖啡师账号没有管理端菜单')
        check('cafe:barista:query' in barista_info['permissions'] and 'cafe:barista:update' in barista_info['permissions'], '咖啡师拥有查看与操作权限')
        check(call('GET', '/admin-api/cafe/menu-item/list', token=barista, success=False)['code'] != 0, '咖啡师不能管理菜单')
        check(call('GET', '/admin-api/infra/file/presigned-url', token=barista, params={'name': 'smoke.png'}, success=False)['code'] != 0, '咖啡师不能使用备用预签名上传接口')
        check(call('POST', '/admin-api/infra/file/create', {'configId': 1, 'path': 'smoke.png', 'name': 'smoke.png', 'url': 'http://localhost:48080/smoke.png'}, token=barista, success=False)['code'] != 0, '咖啡师不能登记直传文件')
        check(call('GET', '/admin-api/system/user/simple-list', token=barista, success=False)['code'] != 0, '咖啡师不能枚举员工目录')
        check(call('GET', '/admin-api/system/user/get-import-template', token=barista, success=False)['code'] != 0, '咖啡师不能下载用户导入模板')
        check(call('GET', '/admin-api/system/user/page', token=manager, success=False)['code'] != 0, '店长不能管理员工账号')
        check(call('GET', '/admin-api/cafe/order/page', token=student_token, success=False)['code'] != 0, '学生令牌不能访问管理端接口')
        check(call('GET', '/app-api/cafe/student/me', token=barista, success=False)['code'] != 0, '员工令牌不能冒充学生')
        check(call('GET', '/admin-api/system/role/simple-list', token=admin), '学校管理员可以使用芋道角色管理')

        # 修改密码必须撤销该用户的旧访问和刷新令牌。
        session_username = 'sess' + RUN
        session_password = 'S' + secrets.token_hex(6)
        session_user_id = call('POST', '/admin-api/system/user/create', {'username': session_username, 'password': session_password, 'nickname': '会话验收', 'deptId': 1, 'postIds': [], 'sex': 0, 'email': '', 'mobile': '', 'remark': '本地接口验收'}, token=admin)
        employees.append(session_user_id)
        call('POST', '/admin-api/system/permission/assign-user-role', {'userId': session_user_id, 'roleIds': [3]}, token=admin)
        old_token = admin_login(session_username, session_password)
        new_password = 'N' + secrets.token_hex(6)
        call('PUT', '/admin-api/system/user/update-password', {'id': session_user_id, 'password': new_password}, token=admin)
        check(call('GET', '/admin-api/system/auth/get-permission-info', token=old_token, success=False)['code'] != 0, '修改密码后旧令牌立即失效')
        check(call('GET', '/admin-api/system/auth/get-permission-info', token=admin_login(session_username, new_password)) is not None, '新密码可正常登录')

        # 店长创建分类、规格和商品，验证实际计价，不改原始菜单。
        code = 'smoke-' + RUN
        category_id = call('POST', '/admin-api/cafe/category/create', {'code': code, 'name': '验收分类', 'nameEn': 'Smoke', 'sort': 99}, token=manager)
        entities.append(('category', category_id))
        group_id = call('POST', '/admin-api/cafe/option-group/create', {'name': '验收温度', 'nameEn': 'Temperature', 'sort': 99, 'options': [{'name': '热', 'nameEn': 'Hot', 'priceDelta': 250, 'isDefault': True, 'sort': 1}]}, token=manager)
        entities.append(('option-group', group_id))
        item = {'name': '验收饮品', 'nameEn': 'Smoke drink', 'description': '', 'descriptionEn': '', 'price': 1000, 'categoryCode': code, 'imageUrl': '/static/menu/latte.jpg', 'recommended': True, 'enabled': True, 'soldOut': False, 'sort': 99, 'groupIds': [group_id]}
        item_id = call('POST', '/admin-api/cafe/menu-item/create', item, token=manager)
        entities.append(('menu-item', item_id))
        item['id'] = item_id
        current_menu = call('GET', '/app-api/cafe/menu')
        selected = next(row for row in current_menu['items'] if row['id'] == item_id)
        option_id = selected['optionGroups'][0]['options'][0]['id']
        check(selected['price'] == 1000, '店长新增商品后学生菜单同步更新')
        settings = {'open': True, 'banner': '接口验收', 'businessHours': [{'start': '00:00', 'end': '24:00'}]}
        call('PUT', '/admin-api/cafe/shop/update', settings, token=manager)
        check(call('GET', '/app-api/cafe/shop/status')['open'], '店长可维护营业时段与营业开关')
        payload = {'items': [{'itemId': item_id, 'quantity': 2, 'optionIds': [option_id]}]}
        order = call('POST', '/app-api/cafe/order/create', payload, token=student_token, key='normal-' + RUN)
        check(order['status'] == 10 and order['totalPrice'] == 2500, '服务端按商品价与规格加价计算金额，支付成功后待录单')
        check(call('GET', '/app-api/cafe/student/me', token=student_token)['balance'] == MOCK_INITIAL_BALANCE - 2500,
              '下单扣除 25 元学生卡余额')
        check(isinstance(order['createTime'], int), '订单时间为毫秒时间戳')
        replay = call('POST', '/app-api/cafe/order/create', payload, token=student_token, key='normal-' + RUN)
        check(replay['id'] == order['id']
              and call('GET', '/app-api/cafe/student/me', token=student_token)['balance'] == MOCK_INITIAL_BALANCE - 2500,
              '同一幂等标识只创建订单、扣款一次')
        conflict = {'items': [{'itemId': item_id, 'quantity': 1, 'optionIds': [option_id]}]}
        check(call('POST', '/app-api/cafe/order/create', conflict, token=student_token, key='normal-' + RUN, success=False)['code'] != 0, '相同幂等标识且商品内容不同会拒绝')
        board = call('GET', '/admin-api/cafe/barista/order/board', token=barista)
        check(any(row['id'] == order['id'] for row in board['waiting']), '咖啡师端出现待录单的 App 订单')
        check(order['aheadCount'] is not None, '当天进行中的订单附带前面单数')
        pos = 'S' + secrets.token_hex(5)
        call('PUT', '/admin-api/cafe/barista/order/enter', {'id': order['id'], 'posOrderNo': ' ' + pos + ' '}, token=barista)
        current = next(row for row in app_page(student_token) if row['id'] == order['id'])
        check(current['status'] == 20 and current['posOrderNo'] == pos and current['enteredTime'], '回填去掉首尾空格，学生看到收银单号和制作中')
        corrected = pos + 'A'
        call('PUT', '/admin-api/cafe/barista/order/enter', {'id': order['id'], 'posOrderNo': corrected}, token=barista)
        check(next(row for row in app_page(student_token) if row['id'] == order['id'])['posOrderNo'] == corrected, '制作中的收银单号可更正')
        call('PUT', '/admin-api/cafe/barista/order/done', {'id': order['id']}, token=barista)
        current = next(row for row in app_page(student_token) if row['id'] == order['id'])
        check(current['status'] == 30 and current['doneTime'] and current['aheadCount'] is None, '制作完成后学生可见完成时间，前面单数为空')
        check(call('PUT', '/admin-api/cafe/barista/order/done', {'id': order['id']}, token=barista, success=False)['code'] != 0, '重复制作完成会提示订单状态已变化')
        call('PUT', '/admin-api/cafe/barista/order/undo-done', {'id': order['id']}, token=barista)
        current = next(row for row in app_page(student_token) if row['id'] == order['id'])
        check(current['status'] == 20 and current['doneTime'] is None, '当天制作完成可撤回，完成时间被清空')
        call('PUT', '/admin-api/cafe/barista/order/done', {'id': order['id']}, token=barista)
        # 编辑现价不会改变订单快照。
        item['name'] = '验收饮品已改名'
        item['price'] = 3000
        call('PUT', '/admin-api/cafe/menu-item/update', item, token=manager)
        historical = next(row for row in app_page(student_token) if row['id'] == order['id'])
        check(historical['items'][0]['name'] == '验收饮品' and historical['totalPrice'] == 2500, '修改菜单不影响已下单的商品与金额快照')
        settings['open'] = False
        call('PUT', '/admin-api/cafe/shop/update', settings, token=manager)
        check(call('POST', '/app-api/cafe/order/create', payload, token=student_token, key='closed-' + RUN, success=False)['code'] != 0, '营业开关关闭时拒绝新订单')
        settings['open'] = True
        settings['businessHours'] = []
        call('PUT', '/admin-api/cafe/shop/update', settings, token=manager)
        check(call('POST', '/app-api/cafe/order/create', payload, token=student_token, key='outside-' + RUN, success=False)['code'] != 0, '不在营业时段时拒绝下单')
        settings['businessHours'] = [{'start': '00:00', 'end': '24:00'}]
        call('PUT', '/admin-api/cafe/shop/update', settings, token=manager)
        # 默认余额可购买两单 10 个芝士蛋糕，第三单明确余额不足。
        low_no = 'LOW' + RUN
        low_token = call('POST', '/app-api/cafe/auth/dev-login', {'studentNo': low_no, 'name': '验收余额不足'}, dev_secret=True)['accessToken']
        bakery = next(row for row in menu['items'] if row['name'] == '巴斯克芝士蛋糕')
        large = {'items': [{'itemId': bakery['id'], 'quantity': 10, 'optionIds': []}]}
        affordable_orders = MOCK_INITIAL_BALANCE // (bakery['price'] * 10)
        paid = [call('POST', '/app-api/cafe/order/create', large, token=low_token, key=f'low-{index}-{RUN}')
                for index in range(affordable_orders)]
        failure = call('POST', '/app-api/cafe/order/create', large, token=low_token, key='insufficient-' + RUN, success=False)
        check(failure['code'] == 1080003002, '余额不足明确拒绝下单')
        check(len(app_page(low_token)) == affordable_orders, '学生端不显示支付失败订单')
        # 同日收银单号唯一，重复失败后仍保持待录单。
        duplicate = call('PUT', '/admin-api/cafe/barista/order/enter', {'id': paid[0]['id'], 'posOrderNo': corrected}, token=barista, success=False)
        check(duplicate['code'] == 1080004003, '数据库约束阻止当天重复收银单号')
        for index, row in enumerate(paid):
            call('PUT', '/admin-api/cafe/barista/order/enter', {'id': row['id'], 'posOrderNo': 'L' + RUN[:10] + str(index)}, token=barista)
            call('PUT', '/admin-api/cafe/barista/order/done', {'id': row['id']}, token=barista)
        failed = call('GET', '/admin-api/cafe/order/page', token=manager, params={'student': low_no, 'status': 1})
        check(failed['total'] == 1, '管理端可筛选支付失败订单')
        board = call('GET', '/admin-api/cafe/barista/order/board', token=barista)
        check(all(row['status'] in (10, 20, 30) for group in board.values() for row in group), '咖啡师接口不返回内部支付状态')
        today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime('%Y-%m-%d')
        params = {'student': student_no, 'startDate': today, 'endDate': today, 'status': 30, 'posOrderNo': corrected}
        stats = call('GET', '/admin-api/cafe/order/statistics', token=manager, params=params)
        check(stats == {'orderCount': 1, 'totalPrice': 2500, 'paidAmount': 2500}, '日期、状态、学号和收银单号筛选的统计金额正确')
        request = urllib.request.Request(ADMIN_BASE + '/admin-api/cafe/order/export-excel?' + urllib.parse.urlencode(params), headers={'Authorization': 'Bearer ' + manager})
        with urllib.request.urlopen(request, timeout=30) as response:
            exported = response.read()
        with zipfile.ZipFile(io.BytesIO(exported)) as workbook:
            xml = ''.join(workbook.read(name).decode() for name in workbook.namelist() if name.endswith('.xml'))
        check(order['orderNo'] in xml, '店长可导出筛选结果为有效 Excel 工作簿')
        check(call('GET', '/app-api/cafe/order/queue', token=student_token)['waitingCount'] >= 0, '排队单数接口返回当天排队单数')
        print(f'\n全部通过：{checks} 项。运行标识：{RUN}')
    finally:
        # 尽力完成所有清理，某一项失败不阻止其他资源还原。
        errors = []
        cleanup = [('营业设置', lambda: call('PUT', '/admin-api/cafe/shop/update', {key: original_shop[key] for key in ('open', 'banner', 'businessHours')}, token=admin))]
        for entity, entity_id in sorted(entities, key=lambda row: {'menu-item': 0, 'option-group': 1, 'category': 2}[row[0]]):
            cleanup.append((entity, lambda entity=entity, entity_id=entity_id: call('DELETE', '/admin-api/cafe/' + entity + '/delete', token=admin, params={'id': entity_id})))
        for user_id in employees:
            cleanup.append(('员工账号', lambda user_id=user_id: call('DELETE', '/admin-api/system/user/delete', token=admin, params={'id': user_id})))
        for name, action in cleanup:
            try:
                action()
            except Exception as error:
                errors.append(f'{name}: {error}')
        if errors:
            raise RuntimeError('清理未完成，请检查：' + '; '.join(errors))


if __name__ == '__main__':
    run()
