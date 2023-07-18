# Grid

## Configuration

To enable or disable searcher, update `config.yml` and set "enabled" as `True` or `False`.

```yaml
searchers:
  grid_company:        # <<< Note this must be identical to the id
    id: grid_company
    name: Grid API Company Search
    hint: Enter a company to search for
    tooltip: Get the Grid API information of a company
    enabled: True
  grid_people:
    id: grid_people
    name: Grid API People Search
    hint: Enter the name of a person to search for
    tooltip: Get the Grid API information of a person
    enabled: True

```

## Adaptors

### Grid

GRID is a diligence technology provider with a SaaS solution that supports screening of business relationships against the MA KYC proprietary GRID™ database. As such, MA KYC delivers powerful, decision-ready intelligence and world class risk and compliance protection, allowing global organizations to identify banned / suspect entities, strengthen fraud protection, ensure regulatory compliance, manage supply and distribution risk and protect their brand equity.

This adaptor allows Videris users to search for the Grid information of a company or person. If the company is found in Grid, information like Name, Status, Address, Risk Score, Incorporation Date are returned. If the person is found in Grid, information like First Name, Last Name, Nationality, Date of Birth, Risk Score are returned.


## Enabling the adaptor

The adaptor is written in Python 3.10 and makes use of the [FastAPI](https://fastapi.tiangolo.com/) framework which runs on a [uvicorn](https://www.uvicorn.org/) server.

Install the required packages:

```
pip install -r requirements.txt
```

Configure mandatory environment variables:

```
export GRID_API_USERNAME='XX000000'
export GRID_API_PASSWORD='YY000000'
```

Additionally, you can configure these optional environment variables if you want to alter the default behavior:

```
export GRID_TOKEN_FILE_PATH='/the/new/path/to/grid-token.json'
```

Run API on the uvicorn server:

```
uvicorn main:app --host <IPv4 address>
```

The IPv4 ip address needs to be accessible to Videris, so make sure you configure any necessary port forwarding rules.
