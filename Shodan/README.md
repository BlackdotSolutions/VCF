# README

This README documents steps that are necessary to get the application up and running.

## Ruby version
ruby "3.0.2"


## System dependencies
    
    gem 'shodan'
    gem 'uri'
    gem 'securerandom'

## Configuration
The main code is found at [app/controllers/application_controller.rb](app/controllers/application_controller.rb). You'll need to add your own API Key to line 8 of this file.

In the root of directory run

    bundle install  

And to bind your server to port 3010 and your IP
    
    rails server -p 3010 --binding=<IP-OF-YOUR-HOST>

e.g.
    
    rails server -p 3010 --binding=10.211.55.2


## Deployment instructions
Once your endpoind is running, open a browser and enter the following (ensure you update the port & IP) to test the system:
http://10.211.55.2:3010/searchers/Videris123/results?query=VSAT&maxResults=100

## Changes
Any changes to how the endpoint is routed are made in [config/routes.rb](config/routes.rb)

The main code is found at [app/controllers/application_controller.rb](app/controllers/application_controller.rb)
