from flask import Flask, render_template, request, send_from_directory
from common import *
import os
from account import account
app = Flask(__name__, template_folder='./pages/templates')
ENV = os.getenv('ENV')
if isinstance(ENV, str):
    if ENV not in ['PROD', 'DEV']:
        ENV = 'DEV'
else:
    ENV = 'DEV'

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html')
    data = request.form.get('textarea')
    if any(['Paste Contents of MyStudentData File Here' in data, data == '']):
        return render_template('index.html')
    try:
        print(f'Attempting to read data')
        loans_obj = account(data.strip())
        console_print = str(
            '\n'.join(loans_obj.print_loans_summary()) +
            '\n'.join(loans_obj.print_all_loan_details())
        ).replace('\n','<br>')
        print(f'Success reading data')
    except Exception as e:
        app.logger.critical(f'Error reading data: {e}')
        console_print = 'Error reading data'
    return console_print

if __name__ == '__main__':
    print(f'Running in {ENV} mode')
    if ENV == 'PROD':
        app.run(ssl_context=('cert.pem', 'privkey.pem'), port=443, host='0.0.0.0')
    else:
        app.run(debug=True, ssl_context='adhoc')