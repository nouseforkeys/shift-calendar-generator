"""
creates calendar events for shift work
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from uuid import uuid4, UUID


log = logging.getLogger(Path(__file__).name)
logging.basicConfig(level=logging.INFO)


@dataclass
class Event:
    """container for an event"""
    organiser: str
    dtstart: datetime
    dtend: datetime
    summary: str
    dtstamp: datetime = None
    uid: UUID = None

    DT_FORMAT = '%Y%m%dT%H%M%S'

    def __post_init__(self):
        if self.uid is None:
            self.uid = uuid4()
        if self.dtstamp is None:
            self.dtstamp = datetime.now()

    def to_str(self) -> str:
        """
        converts this object to the event portion of an iCalendar file string
        """
        content = ['BEGIN:VEVENT']
        content.append(f'UID:{self.uid}')
        content.append(f'ORGANIZER:{self.organiser}')
        content.append(f'DTSTAMP:{self.dtstamp.strftime(self.DT_FORMAT)}')
        content.append(f'DTSTART:{self.dtstart.strftime(self.DT_FORMAT)}')
        content.append(f'DTEND:{self.dtend.strftime(self.DT_FORMAT)}')
        content.append(f'SUMMARY:{self.summary}')
        content.append('END:VEVENT')

        return '\n'.join(content)


@dataclass
class Calendar:
    """basis for creating an iCalendar event file"""
    prodid: str
    version: str = '2.0'
    events: list[Event] = None

    def __post_init__(self):
        if self.events is None:
            self.events = list()

    def to_str(self) -> str:
        """converts this object to an iCalendar file string"""
        content = ['BEGIN:VCALENDAR']
        content.append(f'VERSION:{self.version}')
        content.append(f'PRODID:{self.prodid}')
        for event in self.events:
            content.append(event.to_str())
        content.append('END:VCALENDAR')

        return '\n'.join(content)

    def to_file(self, filename: Path) -> None:
        """saves this object to an iCalendar file"""
        save_to = filename.with_suffix('.ics')
        with open(save_to, 'w') as file:
            file.write(self.to_str())
        log.info(f'saved to "{save_to}"')


c = Calendar(prodid=Path(__file__).name)
print(c)
for day in range(4, 6):
    c.events.append(Event(
        'Admo',
        datetime(year=2025, month=6, day=day),
        datetime(year=2025, month=6, day=day+1),
        'stuff'
    ))
print(c)
output_dir = Path('outputs')
output_dir.mkdir(exist_ok=True)
c.to_file(output_dir / 'test')
