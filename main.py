from flask import Flask, render_template, request
from loan_reader import *
app = Flask(__name__, template_folder='./pages/templates')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html')
    data = request.form.get('textarea')
    loans_obj = loans(data.strip())
    console_print = str(
        '\n'.join(loans_obj.print_loans_summary()) +
        '\n'.join(loans_obj.print_all_loan_details()) +
        '\n'.join(loans_obj.print_longest_payment_chains())
    ).replace('\n','<br>')
    return console_print

if __name__ == '__main__':
    app.run(debug=True)