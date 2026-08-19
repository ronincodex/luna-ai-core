from .weather import WeatherTool
from .traffic import TrafficTool
from .calendar import CalendarTool
from .messaging import MessagingTool
from .email import EmailTool  # <-- new

TOOLS = {
    "get_weather": WeatherTool(),
    "get_traffic": TrafficTool(),
    "create_reminder": CalendarTool(),
    "send_message": MessagingTool(),
    "send_email": EmailTool(),  # <-- new
}
