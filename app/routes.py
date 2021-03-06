import atexit
from urllib.parse import urlparse
from flask import request, render_template, redirect, abort
from app import app, edCoder, database, validator

hostname = app.config['HOST']
CON, CUR, DB = database.init_db_conn()


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_url = request.form.get('url')
        if urlparse(original_url).scheme == '':
            original_url = 'http://' + original_url
        is_valid = validator.is_valid_input(original_url)
        if is_valid is None:
            abort(500)
        insert_record = """
                INSERT INTO tiny(url) VALUES('%s') RETURNING id;
                """ % original_url
        DB(insert_record)
        CON.commit()
        result_cursor = CUR.fetchone()[0]
        encoded_string = edCoder.to_base_62(result_cursor)
        return render_template('home.html', tiny_url=hostname + encoded_string)
    return render_template('home.html')


@app.route('/api-create')
def api_create():
    url = request.args.get('url')
    if url is None or url == '':
        abort(500)
    if urlparse(url).scheme == '':
        url = 'http://' + url
    is_valid = validator.is_valid_input(url)
    if is_valid is None:
        abort(500)
    insert_record = """
            INSERT INTO tiny(url) VALUES('%s') RETURNING id;
            """ % url
    DB(insert_record)
    CON.commit()
    result_cursor = CUR.fetchone()[0]
    encoded_string = edCoder.to_base_62(result_cursor)
    tiny_url = hostname + encoded_string
    return tiny_url


@app.route('/<tiny_url>')
def redirect_tiny_url(tiny_url):
    decoded_string = edCoder.to_base_10(tiny_url)
    redirect_url = hostname
    select_record = """
            SELECT url FROM tiny WHERE ID=%s;
            """ % decoded_string
    DB(select_record)
    try:
        redirect_url = CUR.fetchone()[0]
    except Exception as error:
        print(error)
    return redirect(redirect_url)


@atexit.register
def end():
    app.logger.info('Shutting app down')
    CUR.close()
