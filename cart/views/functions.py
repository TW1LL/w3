from cart.models import ShoppingCart
from django.core.mail import EmailMultiAlternatives
import easypost, json, stripe
from django.conf import settings as siteSettings

if siteSettings.DEBUG == True:
    easypost.api_key = 'PtuiK6fa0pnWTL9cVMbT4A'
    stripe.api_key = 'sk_test_rkjc0dbKQXNuxKL8Vv3ufwBl'

else:
    easypost.api_key = '9bu7oUwgGAhvXJbG6IvqPQ'
    stripe.api_key = 'sk_live_Hic99hSOWFmRHzeuCgOiXvIS'


def stripeToken():
    if siteSettings.DEBUG is True:
        return 'pk_test_zYPD04M9BfHgurntkeskiIRr'
    else:
        return 'pk_live_RcuDbpBGm72ekMijPkNHr4xO'


def viewVars(request = None):
    page = { 'title': 'w3', 'slogan': 'Swinging on a bananaaaaa' }
    
    page['nav'] = [{'link' : '/', 'title' : 'Home'}, 
                   {'link' : '/product', 'title' : 'Products' }]
    page['usernav'] = {'dropdown':[{},{}]}
   
   
    cart_count = 0
    page['user'] = None
    page['usernav']['title'] = 'Account'
    page['usernav']['dropdown'][0] = {'link': '/account/register', 'title': 'Register'}
    page['usernav']['dropdown'][1] = {'link': '/account/login', 'title': 'Login'}
    # Changes navbar items if logged in
    if(request == None):
        pass
    else:
        if(request.user.is_authenticated()):
            page['user'] = request.user
            page['usernav']['title'] = request.user.username
            page['usernav']['dropdown'][0] = {'link': '/account', 'title': 'Account'}
            page['usernav']['dropdown'][1] = {'link': '/account/logout', 'title': 'Logout'}
            cart_count = len(ShoppingCart.objects.filter(owner = request.user.id))
        else:
            cart_count = 0
            page['user'] = None
            page['usernav']['title'] = 'Account'
            page['usernav']['dropdown'][0] = {'link': '/account/register', 'title': 'Register'}
            page['usernav']['dropdown'][1] = {'link': '/account/login', 'title': 'Login'}
        
    return {'page' : page, 'cart_count' : cart_count }



class Shipment():

    def create_shipment(self, address):

        self.fromAddress = easypost.Address.create(
          company = 'Wagner Co.',
          street1 = '12 Hawk Drive',
          city = 'West Windsor',
          state = 'NJ',
          zip = '08550',
          phone = '609-468-0142'
        )
        self.parcel = easypost.Parcel.create(
            predefined_package = 'SmallFlatRateBox',
            weight = 10
        )
        if address != None:
            self.toAddress = easypost.Address.create(name= address[0],company= address[1],street1 = address[2], city = address[3], state = address[4], zip = address[5])
            self.shipment = easypost.Shipment.create(to_address = self.toAddress, from_address = self.fromAddress, parcel = self.parcel)

        self.toAddress = easypost.Address.create(name= address[0],company= address[1],street1 = address[2], city = address[3], state = address[4], zip = address[5])

        self.shipment = easypost.Shipment.create(to_address = self.toAddress, from_address = self.fromAddress, parcel = self.parcel)
        return self.shipment
    
    def view_rates(self, id = None):
        return self.shipment.rates
        
    def buy(self, shipment):
        shipment = json.loads(shipment)
        self.shipment = easypost.Shipment.retrieve(shipment['shipment_id'])
        self.shipment.buy(rate={'id': shipment['id']})
        return [self.shipment.postage_label.label_url, self.shipment.tracking_code]
        

def send_email(email):
    msg = EmailMultiAlternatives(email['subject'], email['text'], email['from'], [email['to']])
    msg.attach_alternative(email['html'], "text/html")
    msg.send()

ezpost = Shipment()
