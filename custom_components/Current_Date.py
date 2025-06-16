from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

from loguru import logger

from langflow.custom import Component
from langflow.io import DropdownInput, Output
from langflow.schema.message import Message


class CurrentDateComponent(Component):
    display_name = "Current Date"
    description = "Returns the current date and time in the selected timezone."
    icon = "clock"
    name = "CurrentDate"

    inputs = [
        DropdownInput(
            name="timezone",
            display_name="Timezone",
            options=list(available_timezones()),
            value="UTC",
            info="Select the timezone for the current date and time.",
            tool_mode=True,
        ),
    ]
    outputs = [
        Output(display_name="Current Date", name="current_date", method="get_current_date"),
    ]

    def get_current_date(self) -> Message:
        try:
            tz = ZoneInfo(self.timezone)
            current_date_str = datetime.now(tz).strftime("%Y-%m-%d")
            full_message_text = f"Current date in {self.timezone}: {datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")}"
            self.status = full_message_text
            return Message(text=current_date_str, data={"full_date_info": full_message_text, "date_simple": current_date_str})
        except Exception as e:  # noqa: BLE001
            logger.opt(exception=True).debug("Error getting current date")
            error_message = f"Error: {e}"
            self.status = error_message
            return Message(text=error_message)
