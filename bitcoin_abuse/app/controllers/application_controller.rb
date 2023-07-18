require 'uri'
require 'securerandom'
require 'net/http'
require 'json'

class ApplicationController < ActionController::API

  def index
    # Bitcoin Abuse setup
    apiBitcoinAbuse = '<API-Key>'

    out_data = []

    if request.query_parameters['query']
      if request.fullpath[/Videris124/]
        uri = URI("https://www.bitcoinabuse.com/api/reports/check?address=#{request.query_parameters['query']}&api_token=#{apiBitcoinAbuse}")
        res = Net::HTTP.get_response(uri)
        r = res.body
        data = JSON.parse(r)
        if request.query_parameters['maxResults']
          summary = data['recent']
          summary.each do |s|
            x = s.to_s.split(',')
            seedID = SecureRandom.uuid
            bcaID = SecureRandom.uuid
            bcID = SecureRandom.uuid
            out_data << {
              "key" => "#{SecureRandom.uuid}".to_s.upcase,
              "title" => data['address'],
              "subTitle" => "First seen: #{data['first_seen']} & Last seen: #{data['last_seen']}",
              "summary" => x.join(",").to_s.delete("\"{}}"),
              "source"=> "Bitcoin Abuse",
              "entities" => [
                {
                  "id"=> "#{seedID}",
                  "type"=> "EntityAsset",
                  "attributes"=> {
                    "Data"=> data['address'],
                    "Name"=> data['address']
                  }
                },
                {
                  "id"=> "#{bcaID}",
                  "type"=> "EntityWebPage",
                  "attributes"=> {
                    "Data"=> "https://bitcoinabuse.com/reports/#{request.query_parameters['query']}",
                    "Url"=> "https://bitcoinabuse.com/reports/#{request.query_parameters['query']}"
                  }
                },
                {
                  "id"=> "#{bcID}",
                  "type"=> "EntityWebPage",
                  "attributes"=> {
                    "Data"=> "https://www.blockchain.com/btc/address/#{request.query_parameters['query']}",
                    "Url"=> "https://www.blockchain.com/btc/address/#{request.query_parameters['query']}"
                  }
                },
                {
                  "id"=> "#{SecureRandom.uuid}",
                  "type"=> "RelationshipRelationship",
                  "attributes"=> {
                    "Direction"=> "FromTo",
                    "FromId"=> "#{seedID}",
                    "Title"=> "Abuse Report",
                    "ToId"=> "#{bcaID}"
                  }
                },
                {
                  "id"=> "#{SecureRandom.uuid}",
                  "type"=> "RelationshipRelationship",
                  "attributes"=> {
                    "Direction"=> "FromTo",
                    "FromId"=> "#{seedID}",
                    "Title"=> "Wallet Summary",
                    "ToId"=> "#{bcID}"
                  }
                },
              ],
              "url"=> "https://bitcoinabuse.com/reports/#{request.query_parameters['query']}"
            }
          end
        end
      end
      render json: {"searchResults" => out_data}
    else
      out_data << {
      "id" => "Videris124",
      "name" => "Bitcoin Abuse",
      "hint" => "Check for abused Bitcoin wallets",
      "tooltip"=> "Search for Bitcoin wallets that have been abused"
      }
      render json: out_data.to_json
    end
  end
end
