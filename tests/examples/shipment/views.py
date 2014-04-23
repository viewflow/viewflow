from viewflow.flow import start


class StartView(start.StartView):
    def save_process(self):
        self.process.created_by = self.request.user
        return super(StartView, self).save_process()
