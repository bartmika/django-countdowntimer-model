# django-countdowntimer-model

## About

The goal of this library is to allow you to inherit an abstract model in your model and turn it into a countdown time with pause and resume capability.

Simply import, inherit and your model is now a timer without worrying about the complexity involved in timekeeping.

This library is written to return the countdown value based on timestamps and thus does not require complicated background *tick* processes.


## Minimum Requirements

* Python 3.7

* Django 3.0.5


## Installation

Run the following in your project.

```
pip install django-countdowntimer-model
```

In your ``settings.p`` file please add:

```
INSTALLED_APPS = [

    # ...

    "countdowntimer_model",

    # ...
]
```


## Usage

First you must import the abstraction into your ``model`` file.

```python
from countdowntimer_model.models import CountdownTimer
```

Afterwords your model must inherit the abstraction.

```python
class DoomsdayCountdownTimer(CountdownTimer):
    # ...
```

When you create your model, it is essential you set the ``duration_in_minutes``
and ``state`` fields. Afterwords the model will handle the rest. Please note
if you want to override to use a custom timezone then you can set the
``timezone_override`` field.

```python
doomsday_timer = DoomsdayCountdownTimer.object.create(
    duration_in_minutes=123,
    state=DoomsdayCountdownTimer.STATE.RUNNING,
)
```

Now that the object has been created you can get the latest countdown by running
the following:

```python
remaining_t = doomsday_timer.remaining_time() # // Returned in `time` format.
```

or

```python
remaining_minutes = doomsday_timer.remaining_time_in_minutes() # // Returned in `integer` format.


## License

This library is licensed under the **BSD 2-Clause License**. See [LICENSE.md](LICENSE) for more information.
