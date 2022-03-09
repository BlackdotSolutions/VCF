require 'shodan'
require 'uri'
require 'securerandom'

class ApplicationController < ActionController::API

  def index
    api = Shodan::Shodan.new('tesTPDEqHqXSW8ItgL6I0K6jddQWNdNs')
    out_data = []

    if request.query_parameters['query']
      if request.fullpath[/Videris123/]
        data = api.search(request.query_parameters['query'])
        if request.query_parameters['maxResults']
          data['matches'].each_with_index do |val, index|
            if index < request.query_parameters['maxResults'].to_i
              out_data << {
                "key" => "#{SecureRandom.uuid}".to_s.upcase,
                "title" => val['ip_str'],
                "subTitle" => "#{val['org']} - #{val['location']['country_name']}",
                "summary" => val['data'],
                "source"=> "Shodan",
                "entities" => [
                  {
                    "id"=> "#{SecureRandom.uuid}",
                    "type"=> "EntityIpAddress",
                    "attributes"=> {
                      "IpAddress"=> val['ip_str'],
                      "Name"=> val['org'],
                      "City"=> val['location']['city'],
                      "Country"=> val['location']['country_name']
                    }
                  }
                ],
                "url"=> "https://shodan.io/search?query=#{request.query_parameters['query']}"
              }
            end
          end
          if data['total'].to_i > request.query_parameters['maxResults'].to_i
            data['total'] = request.query_parameters['maxResults']
          end
        end
      end
      render json: {"searchResults" => out_data}
    else
      out_data << {
      "id" => "Videris123",
      "name" => "Shodan.io",
      "hint" => "Search IoT devices on shodan.io",
      "tooltip"=> "Search IoT with shodan.io"
      }
      render json: out_data.to_json
    end
  end
end
