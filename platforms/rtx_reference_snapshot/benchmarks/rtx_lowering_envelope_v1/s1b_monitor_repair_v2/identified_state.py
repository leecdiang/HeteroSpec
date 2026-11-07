from bounded import State

class IdentifiedState(State):
    def __init__(self,root,stage,run_id,execution_id):
        super().__init__(root,stage);self.run_id=run_id;self.execution_id=execution_id;self.worker=None
    def snapshot(self,status):
        r=super().snapshot(status)
        r.update(run_id=self.run_id,execution_id=self.execution_id,conservative_owned_seconds=5*r['seconds'],process_bound_multiplier=5)
        return r
