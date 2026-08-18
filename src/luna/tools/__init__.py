from .weather import WeatherTool
from .traffic import TrafficTool
from .calendar import CalendarTool
from .messaging import MessagingTool

TOOLS = {
    "get_weather": WeatherTool(),
    "get_traffic": TrafficTool(),
    "create_reminder": CalendarTool(),
    "send_message": MessagingTool(),
}
