import os
from icalendar import Calendar
from datetime import datetime, timedelta



# Chemin vers le dossier des calendriers Ubuntu
calendar_dir = os.path.expanduser('~/.local/share/evolution/calendar/system')





def recuperer_event(duree):
    # Date de d�but et de fin pour la recherche d'�v�nements (une semaine)
    start_date = datetime.now()
    end_date = start_date + timedelta(days=duree)

    events = []

    # Parcourir tous les fichiers .ics dans le dossier des calendriers
    for filename in os.listdir(calendar_dir):
        if filename.endswith('.ics'):
            with open(os.path.join(calendar_dir, filename), 'rb') as file:
                cal = Calendar.from_ical(file.read())
                for component in cal.walk():
                    if component.name == "VEVENT":
                        event_start = component.get('dtstart').dt
                        event_end = component.get('dtend').dt
                        
                        # Convertir en datetime si n�cessaire
                        if isinstance(event_start, datetime):
                            event_start_date = event_start.date()
                        else:
                            event_start_date = event_start
                        
                        if isinstance(event_end, datetime):
                            event_end_date = event_end.date()
                        else:
                            event_end_date = event_end
                        
                        # V�rifier si l'�v�nement est dans la plage de dates
                        if start_date.date() <= event_start_date <= end_date.date() or start_date.date() <= event_end_date <= end_date.date():
                            events.append({
                                'summary': str(component.get('summary')),
                                'start': event_start,
                                'end': event_end,
                                'description': str(component.get('description', 'Pas de description'))
                            })

    return events


