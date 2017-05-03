from celery.task import task


class Algorithm:
    """Base class for a Data Cube algorithm

    This will serve as the base class for any Data Cube algorithm.
    An algorithm is defined as:
        parse_parameters_from_task: A task that parses out required parameters from a Task model, implemented on the app level
        perform_task_chunking: A task that chunks parameter sets into manageable sizes using the result of parse_parameters_from_task
        --some number of tasks that operate on the requested data--
        recombine_chunks_and_update_task: A task that takes the chunked datasets' results, combines them into a single result, and
            updates the task model.
    """

    task_id = None

    def __init__(self, _id):
        self.task_id = _id

    def run(self):
        """
        """
        print("RUNNING QUERY")
        print(self.task_id)
        self.parse_parameters_from_task.delay(self.task_id)
        return True

    @task(name="app_name.parse_parameters_from_task")
    def parse_parameters_from_task(task_id):
        """
        """
        print(task_id)

        parameters = {}
        return parameters

    @task(name="app_name.perform_task_chunking")
    def perform_task_chunking(parameter_set):
        """
        """
        pass

    @task(name="app_name.recombine_chunks_and_update_task")
    def recombine_chunks_and_update_task(chunks):
        """
        """
        pass

    """
    Processing pipeline definitions
    """

    @task(name="app_name.load_and_mask_data")
    def load_and_mask_data(**kwargs):
        """
        """
        pass

    @task(name="app_name.mosaic_data")
    def create_mosaic(dataset):
        """
        """
        pass
