from viewflow import site, flow, this, Flow
from order import models, views, tasks


class TravelRequest(flow.Flow):
    # Applicant
    start = flow.Start() \
        .Activate(this.split_allow_cancel)

    split_allow_cancel = flow.Split() \
        .Next(views.cancel_request) \
        .Next(views.register_request)

    register_request = flow.View(views.register_request) \
        .Next(views.approve_request)
    
    # Supervisor
    approve_request = flow.View(views.approve_request) \
        .Next(this.is_approved)

    is_approved = flow.Switch() \
        .Case(approve_request, cond=lambda process: process.modifiction_required()) \
        .Case(tasks.notify_rejection, cond=lambda process: process.rejected()) \
        .Case(this.run_booking_actions, cond=lambda process: process.approved())

    notify_rejection = flow.Job(tasks.notify_rejection) \
        .Next(this.rejected)

    rejected = End()

    # Travel Agent
    this.run_booking_actions = flow.Split() \
        .Next(views.book_hotel, cond=lambda process: process.have_hotel()) \
        .Next(view.book_flight, cond=lambda process: process.have_flight())

    book_hotel = flow.View(views.have_hotel) \
        .Next(this.end_booking_actions)

    book_flight = flow.View(views.have_flight) \
        .Next(this.end_booking_actions)

    end_booking_actions = flow.Join(wait_all=True) \
        .Next(tasks.get_exchange_rate)

    get_exchange_rate = flow.Job(tasks.get_exchange_rate) \
        .Next(tasks.send_travel_info)

    send_travel_info = flow.Job(tasks.send_travel_info) \
        .Next(views.issue_advance)

    # Accouting
    issue_advance = flow.View(issue_advance) \
        .Next(request_complete)

    request_complete = flow.End()

