from flask import Blueprint, request, jsonify

alice = Blueprint('alice', __name__)


@alice.route('/alice', methods=['POST'])
def alice_func():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'response': {
                    'text': 'Извините, произошла ошибка при обработке запроса.',
                    'end_session': False
                },
                'version': '1.0'
            })

        command = data.get('request', {}).get('command', '').lower()

        if data.get('session', {}).get('new', False) or not command:
            return jsonify({
                'response': {
                    'text': 'Добро пожаловать в TaskMaster! Для работы с задачами необходимо авторизоваться. '
                            'Скажите "войти" для входа или "зарегистрироваться" для создания нового аккаунта.',
                    'end_session': False
                },
                'version': '1.0'
            })

        #Обработка команды регистрации
        if 'зарегистрироваться' in command:
            return jsonify({
                'response': {
                    'text': 'Для регистрации, пожалуйста, используйте веб-интерфейс '
                            'по адресу: https://prankbot.pythonanywhere.com/register',
                    'end_session': False
                },
                'version': '1.0'
            })

        #Обработка команды входа
        if 'войти' in command:
            return jsonify({
                'response': {
                    'text': 'Для входа, пожалуйста, используйте веб-интерфейс '
                            'по адресу: https://prankbot.pythonanywhere.com/login',
                    'end_session': False
                },
                'version': '1.0'
            })

        #Если команда не распознана
        return jsonify({
            'response': {
                'text': 'Извините, я не поняла команду. Для работы с задачами необходимо авторизоваться. '
                        'Скажите "войти" для входа или "зарегистрироваться" для создания нового аккаунта.',
                'end_session': False
            },
            'version': '1.0'
        })

    except Exception as e:
        print(f'error: {str(e)}')
        return jsonify({
            'response': {
                'text': 'Извините, произошла ошибка при обработке запроса.',
                'end_session': False
            },
            'version': '1.0'
        })
