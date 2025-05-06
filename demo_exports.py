from support_platform import _demo_platform, debug_separator


def main():
    platform = _demo_platform(150)
    debug_separator()
    print('Выгружаем все чаты…')
    platform.export_chats(to_file='export/all_chats.json')
    debug_separator()
    print('Выгружаем чаты первого оператора…')
    op = platform.operators[0]
    platform.export_chats(by='operator', value=op, to_file='export/operator_chats.json')
    debug_separator()
    print('Выгружаем чаты первого пользователя…')
    u = platform.users[0]
    platform.export_chats(by='user', value=u, to_file='export/user_chats.json')


if __name__ == '__main__':
    main()
