import requests
import sys
from datetime import datetime, timedelta

year = datetime.now().year


def post(url, data):
    response = requests.post(
        url,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        data=data,
    )
    response.raise_for_status()
    return response.json().get("dataList", [])


def main():
    if len(sys.argv) < 3:
        sys.stderr.write(f"Usage: {sys.argv[0]} <Postcode> <Huisnummer> [Toevoeging]\n")
        sys.exit(1)

    postcode = sys.argv[1]
    huisnummer = sys.argv[2]
    toevoeging = sys.argv[3] if len(sys.argv) > 3 else ""

    address = post(
        "https://twentemilieuapi.ximmio.com/api/FetchAdress",
        {
            "companyCode": "8d97bb56-5afd-4cbc-a651-b4f7314264b4",
            "postCode": postcode,
            "houseNumber": huisnummer,
            "houseLetter": toevoeging,
        },
    )

    if address == []:
        sys.stderr.write("Invalid address:\n")
        sys.stderr.write(f"  postcode: {postcode}\n")
        sys.stderr.write(f"  huisnummer: {huisnummer}\n")
        sys.stderr.write(f"  toevoeging: {toevoeging}\n")
        sys.exit(1)

    address = address[0]

    sys.stderr.write(f"Address {address.get("Street")} {address.get("HouseNumber")} ({address.get("UniqueId")})")
    address_id = address.get("UniqueId")

    calendar_data = post(
        "https://twentemilieuapi.ximmio.com/api/GetCalendar",
        {
            "companyCode": "8d97bb56-5afd-4cbc-a651-b4f7314264b4",
            "uniqueAddressID": address_id,
            "startDate": f"{year}-01-01",
            "endDate": f"{year+2}-01-01",
        },
    )

    events = []
    for entry in calendar_data:
        event_type = entry.get("_pickupTypeText", "Unknown")

        if event_type == "PAPER":
            event_type = "Oud Papier"

        if event_type == "PACKAGES":
            event_type = "Verpakkingen"

        if event_type == "GREEN":
            event_type = "Groen Afval"

        if event_type == "TREE":
            event_type = "Kerstboom"

        for date in entry.get("pickupDates", []):
            date_formatted = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime("%Y%m%d")
            events.append((date_formatted, event_type))

    events.sort()

    # Save to .ics file
    sys.stdout.write("BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//PickupSchedule//EN\n")
    for date, type in events:
        sys.stderr.write(f"{date}: {type}\n")
        sys.stdout.write("BEGIN:VEVENT\n")
        sys.stdout.write(f"SUMMARY:{type}\n")
        sys.stdout.write(f"DTSTART;VALUE=DATE:{date}\n")
        sys.stdout.write(f"DTEND;VALUE=DATE:{date}\n")
        sys.stdout.write("END:VEVENT\n")
    sys.stdout.write("END:VCALENDAR\n")


if __name__ == "__main__":
    main()
