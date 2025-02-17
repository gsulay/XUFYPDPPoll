from flask import Flask, render_template, request, jsonify, make_response
import sqlite3
import datetime
import pandas as pd

app = Flask(__name__)
DEBUG = False

def get_ip():
    #IP Address
    ip_address = request.remote_addr

    # If your app is behind a proxy, you might check 'X-Forwarded-For'
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    return ip_address

@app.route("/vote/<study>")
def vote(study):
    #Check if ip_address is already inside the 
    ip_address = get_ip()

    conn = sqlite3.connect('poll.db')
    cursor = conn.cursor()

    cursor.execute("SELECT ip_address FROM poll")
    results = [i[0] for i in cursor.fetchall()]
    conn.close()

    ip_is_voted = ip_address in results


    #Check if they have already voted using the cookie
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()


    if request.cookies.get('has_voted'):
        cookie_is_voted = True
    else:
        response = make_response(jsonify({"message": "Your vote has been recorded"}))
        response.set_cookie('has_voted', 'true', max_age=60 * 60 * 24 * 7)  #Max Age is 1 week.
        cookie_is_voted = False
    
    category, study_title = study.split('-')

    study_title = " ".join([i.title() for i in study_title.split('_')])
    category = " ".join([i.title() for i in category.split('_')])


    #Add to the database if no cookie is present and ip not found in db
    if ((ip_is_voted == False) and (cookie_is_voted == False)) or DEBUG:
        conn = sqlite3.connect('poll.db')
        cursor = conn.cursor()
        cursor.execute("""
                INSERT INTO poll (criteria, study, ip_address)
                VALUES (?, ?, ?)
            """, (category, study_title, ip_address))
        conn.commit()
        #Add the log
        print('Inserted the values at {}\n{}\t{}\t{}'.format(datetime.datetime.now(),category, study_title, ip_address))
        conn.close()
        return render_template(r'base/voted.html',category = category, study_title = study_title, ip_address = ip_address)

    else:
        print('User has already voted')
        return render_template(r'base/already_voted.html')

@app.route("/livepoll")
def live_poll():
    #Get the data from the database
    conn = sqlite3.connect('poll.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT criteria, study, COUNT(*) as votes
        FROM poll
        GROUP BY criteria, study;
        """)
    
    results = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(results, columns=['Category', 'Study', 'Votes'])
    aggregated = [i.sort_values(by='Votes').values.tolist() for idx, i in df.groupby('Category')]
    print(aggregated)
    return render_template('base/livepoll.html', aggregated = aggregated)



if __name__=="__main__":

    conn = sqlite3.connect('poll.db')
    cursor = conn.cursor()

    #Create a table if exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS poll(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   criteria TEXT NOT NULL,
                   study TEXT NOT NULL,
                   ip_address TEXT NOT NULL)
                   """)
    conn.commit()
    conn.close()
    app.run(debug=True, use_reloader=False)
