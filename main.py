import os
import fix_path
import urllib
import webapp2
import jinja2
from authomatic import Authomatic
from authomatic.adapters import Webapp2Adapter

from config import CONFIG

# Instantiate Authomatic.
authomatic = Authomatic(config=CONFIG, secret='some random secret string')

# Create a simple request handler for the login procedure.


class Login(webapp2.RequestHandler):
    def any(self, provider_name):

        # Log the user in.
        result = authomatic.login(Webapp2Adapter(self), provider_name)

        if result:
            if result.user:
                result.user.update()
                self.response.write('<h1>Hi {0}</h1>'.format(result.user.name))

                # Save the user name and ID to cookies that we can use it in other handlers.
                self.response.set_cookie('user_id', result.user.id)
                self.response.set_cookie('user_name', urllib.quote(result.user.name))

                if result.user.credentials:
                    # Serialize credentials and store it as well.
                    serialized_credentials = result.user.credentials.serialize()
                    self.response.set_cookie('credentials', serialized_credentials)

            elif result.error:
                self.response.set_cookie('error', urllib.quote(result.error.message))

            self.redirect('/')


class Home(webapp2.RequestHandler):
    def get(self):
        # Create links to the Login handler.

        self.response.write('<a href="login/tw">Twitter</a>')

        # Retrieve values from cookies.
        serialized_credentials = self.request.cookies.get('credentials')
        user_id = self.request.cookies.get('user_id')
        user_name = urllib.unquote(self.request.cookies.get('user_name', ''))
        error = urllib.unquote(self.request.cookies.get('error', ''))

        if error:
            self.response.write('<p>Damn that error: {0}</p>'.format(error))
        elif user_id:
            self.response.write('<h1>Hi {0}</h1>'.format(user_name))

            if serialized_credentials:
                # Deserialize credentials.
                credentials = authomatic.credentials(serialized_credentials)

                self.response.write("""
                <p>
                    You are logged in with <b>{0}</b>
                </p>
                """.format(dict(tw='Twitter')[credentials.provider_name]))

                #valid = 'still' if credentials.valid else 'not anymore'
                #expire_soon = 'less' if credentials.expire_soon(60 * 60 * 24) else 'more'
                #remaining = credentials.expire_in
                #expire_on = credentials.expiration_date

                if credentials.valid:
                    self.response.write("""
                    <a href="post/{0}">Post a tweet</a>
                    """.format(credentials.provider_name))
                    self.response.write("""<a href="fetch/{0}">Fetch tweets</a>
                    """.format(credentials.provider_name))
                   
                else:
                    self.response.write("""
                    <p>
                        Repeat the <b>login procedure</b>to get new credentials.
                    </p>
                    <a href="login/{0}">Refresh</a>
                    """.format(credentials.provider_name))
            #self.response.write('<a href="fetch/{0}">Fetch tweets</a>')
            #self.response.write('<p>We can also log you out.</p>')
            self.response.write('<a href="logout">OK, log me out!</a>')

class Post(webapp2.RequestHandler):
    def get(self, provider_name):
        if provider_name == 'tw':
            text = 'tweet'

        self.response.write("""
        <a href="..">Home</a>
        <p>I want to post a {0}.</p>
        <form method="post">
            <input type="text" name="message" value="Twigle is the best Twitter Client :P" />
            <input type="submit" value="Post it!">
        </form>
        """.format(text))
    # To post tweet on user timeline
    def post(self, provider_name):
        self.response.write('<a href="..">Home</a>')

        # Retrieve the message from POST parameters and the values from cookies.
        message = self.request.POST.get('message')
        serialized_credentials = self.request.cookies.get('credentials')
        user_id = self.request.cookies.get('user_id')

        if provider_name == 'tw':

            response = authomatic.access(serialized_credentials,
                                         url='https://api.twitter.com/1.1/statuses/update.json',
                                         params=dict(status=message),
                                         method='POST')

            error = response.data.get('errors')
            tweet_id = response.data.get('id')

            if error:
                self.response.write('<p>Damn that error: {0}!</p>'.format(error))
            elif tweet_id:
                self.response.write("""
                <p>
                    You just tweeted a tweet with id {0}.
                </p>
                """.format(tweet_id))
            else:
                self.response.write("""
                <p>
                    Damn that unknown error! Status code: {0}
                </p>
                """.format(response.status))

        # Let the user repeat the action.
        self.response.write("""
        <form method="post">
            <input type="text" name="message" />
            <input type="submit" value="Post it again!">
        </form>
        """)
            

class Fetch(webapp2.RequestHandler):
    def get(self,provider_name):
        if provider_name=='tw':
            text='tweets'
        self.response.write("""<a href="..">Home</a>
        <p>Fetching {0} from your timeline</p>""".format(text))

        serialized_credentials = self.request.cookies.get('credentials')
        response = authomatic.access(serialized_credentials,
                   url = 'https://api.twitter.com/1.1/statuses/user_timeline.json',
                   method='GET')
        #error = response.data.get('errors')
        #if error:
        #    self.response.write('<p>Damn that error: {0}!</p>'.format(error))
        if response.status == 200:
            if type(response.data) is list:
                for tweet in response.data:
                    text = tweet.get('text')
                    date = tweet.get('created_at')                                                                        
                    self.response.write(u'<h3>{}</h3>'.format(text.replace(u'\u2013', '[???]')))
                    self.response.write(u'Tweeted on: {}'.format(date))
            #elif response.data.get('errors')
            #    self.response.write(u'Damn that error: {}!'.format(response.data.get('errors')))

        else:
            self.response.write('Damn that unknown error!<br />')
            self.response.write(u'Status: {}'.format(response.status))

# Fetch tweets along with replies
class Reply(webapp2.RequestHandler):
    def get(self, provider_name):
        if provider_name =='tw':
            text = 'replies'
        self.response.write("""<a href="..">Home</a>
        <p>Fetching {0} for your tweets</p>""".format(text))
        serialized_credentials = self.request.cookies.get('credentials')
        response = authomatic.access(serialized_credentials,
                url='https://api.twitter.com/1.1/statuses/user_timeline.json',
                method='GET')
        replies = authomatic.access(serialized_credentials,
                url='https://api.twitter.com/1.1/statuses/mentions_timeline.json',
                method='GET')
        if response.status == 200:
            if type(response.data) is list:
                for tweet in response.data:
                    twt_id = tweet.get('id')
                    text = tweet.get('text')
                    date = tweet.get('created_at')                                                                        
                    #self.response.write(u'<br/>Tweet id : {}'.format(twt_id))
                    is_tweet_reply_id = tweet.get('in_reply_to_status_id')
                    if is_tweet_reply_id is None:
                        self.response.write(u'<h3>{}</h3>'.format(text.replace(u'\u2013', '[???]')))
                        self.response.write(u'Tweeted on: {}'.format(date))
                    if replies.status == 200:
                        if type(replies.data) is list:
                            for reply in replies.data:
                                reply_to_status_id = reply.get('in_reply_to_status_id')
                                str_id = reply.get('id_str')
                                if reply_to_status_id == twt_id:
                                    reply_text = reply.get('text')
                                    reply_date = reply.get('created_at')
                                    self.response.write(u'<h5>{}</h5>'.format(reply_text.replace(u'\u2013', '[???]')))
                                    self.response.write(u'Replied on: {}'.format(reply_date))
        else:
            self.response.write('Damn that unknown error!<br />')
            self.response.write(u'Status: {}'.format(response.status))




class Logout(webapp2.RequestHandler):
    def get(self):
        # Delete cookies.
        self.response.delete_cookie('user_id')
        self.response.delete_cookie('user_name')
        self.response.delete_cookie('credentials')

        # Redirect home.
        self.redirect('./')


# Create the routes.
ROUTES = [webapp2.Route(r'/login/<:.*>', Login, handler_method='any'),
          #webapp2.Route(r'/refresh', Refresh),
          webapp2.Route(r'/post/<:.*>', Post),
          webapp2.Route(r'/fetch/<:.*>', Reply),
          webapp2.Route(r'/logout', Logout),
          webapp2.Route(r'/', Home)]

# Instantiate the WSGI application.
app = webapp2.WSGIApplication(ROUTES, debug=True)

