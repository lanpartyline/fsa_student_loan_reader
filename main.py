from flask import Flask, render_template, request
from common import *
import time
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
        loans_obj = account(data.strip())
        console_print = str(
            '\n'.join(loans_obj.print_loans_summary()) +
            '\n'.join(loans_obj.print_all_loan_details())
        ).replace('\n','<br>')
        app.logger.info(f'Success reading data')
    except:
        app.logger.critical(f'Error reading data')
        console_print = 'Error reading data'
    return console_print

if __name__ == '__main__':
    if ENV == 'PROD':
        app.run(ssl_context=('cert.pem', 'privkey.pem'), port=443, host='0.0.0.0')
    else:
        app.run(debug=True, ssl_context='adhoc')
    time.sleep(5)
    app.logger.critical(f'Running in {ENV} mode')