import ordrin
import datetime
import json
import yaml

class OrdrinApi:

    def __init__(self, user_data, production=False):
        if production:
            server = ordrin.PRODUCTION
        else:
            server = ordrin.TEST
        self.ordrin_api = ordrin.APIs(user_data['api_key'], server)
        self.user_data = user_data

    def getRestaurantList(self):
        try:
            response = self.ordrin_api.delivery_list('ASAP',
                    self.user_data['addr'], self.user_data['addr'],
                    self.user_data['zip'])
        except:
            print "Error getting restaurants"
            return None

        return response

    def getRestaurantDetails(self, rid):
        response = self.ordrin_api.restaurant_details(rid)
        return response

    def makeGuestOrder(self, args):
        u = self.user_data
        return self.ordrin_api.order_guest(args['rid'], u['em'], args['tray'],
                args['tip'], u['first_name'], u['last_name'], u['phone'],
                u['zip'], u['addr'], u['city'], u['state'],
                u['card']['number'], u['card']['cvc'], u['card']['expiry'],
                u['card']['bill_addr'], u['card']['bill_city'],
                u['card']['bill_state'], u['card']['bill_zip'],
                u['card']['bill_phone'], card_name = u['card']['name'],
                delivery_date = 'ASAP')

class Item:

    def __init__(self, item):
        self.name = item['name']
        self.price = item['price']
        self.id = item['id']
        self.description = item['descrip']

class Menu:

    def __init__(self, menu):
        self.menu = {}
        categories = self.getCategories(menu)
        for c in categories:
            self.menu[c] = self.getItemsByCategory(c, menu)

    def getCategories(self, menu):
        first = menu[0];

        #Check if we have categories
        if not 'children' in first:
            return None

        categories = []
        for c in menu:
            categories.append(c['name'])
        return categories

    def getItemsByCategory(self, category, menu):
        items = []
        for c in menu:
            if c['name'] != category:
                continue
            for item in c['children']:
                items.append(Item(item))
        return items

class Restaurant:

    def __init__(self, details):
        self.name = details['name']
        self.id = details['restaurant_id']
        self.cuisine = details['cuisine']
        self.addr = details['addr']
        self.city = details['city']
        self.phone = details['cs_contact_phone']
        self.menu = Menu(details['menu'])

class LibOrdrIn:

    def __init__(self, user_info, production=False):
        user_data = self._parseUserInfo(user_info)
        self.api = OrdrinApi(user_data, production)

    def getRestaurants(self):
        restaurants = []
        rlist = self.api.getRestaurantList()
        for r in rlist:
            details = self.api.getRestaurantDetails(str(r['id']))
            restaurants.append(Restaurant(details))
        return restaurants

    def makeOrder(self, rid, items, tip, error=False):
        args = {}
        args['rid'] = rid
        args['tip'] = tip
        args['tray'] = self._generate_tray(items)
        #return self.api.makeGuestOrder(args)
        if not error:
            return { '_error': '0', 'refnum': 'abcc', 'msg': 'Success!',
                    'text': 'Order completed' }
        return { '_error': '1', 'refnum': '-1', 'msg': 'Failed!', 'text': 'We \
        aren\'t open yet!' }

    def _parseUserInfo(self, user_file):
        with open(user_file, 'r') as f:
            user_data = yaml.load(f)
        return user_data

    def _generate_tray(self, items):
        tray_items = []
        for item in items:
            tray_item = "%s/1" % item['id']
            tray_items.append(tray_item)
        return '+'.join(tray_items)
