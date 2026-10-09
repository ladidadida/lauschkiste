# lauschkiste-plugin-time-limits

Quiet hours and a daily listening limit for the box. A plugin for [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids.

In quiet hours (for example from half past seven in the evening to seven in the morning) nothing plays, and
a daily limit fades the sound out and stops the box when the day's time is used up. Parents can add time
for today with one action, which also works from a card.

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version), then
switch it on in the web app (Settings → Plugins) or with:

```bash
lauschctl plugin enable time_limits
```

Documentation: [for builders](https://github.com/ladidadida/lauschkiste/blob/main/documentation/builders/README.md). MIT license.
