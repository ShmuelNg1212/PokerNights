# keep_form keeps every field's data

`groups.http.keep_form` saves each declared field's submitted value in the login session for one redirect. Never pass it a form with a password, token or other secret. The profile's password form keeps only its errors (`request.session["profile_password_errors"]`) and is drawn again with empty data.
