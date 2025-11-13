# Cluster 91

class EvaluationResumeCallback(pl.Callback):
    """Resumes evaluation at the specified epoch number."""

    def __init__(self, epoch_to_resume: int):
        """
        Initialize the callback.
        :param epoch_to_resume: The epoch count of previous evaluation.
        """
        self.epoch_to_resume = epoch_to_resume
        assert self.epoch_to_resume >= 0, f'Invalid epoch number to resume: {self.epoch_to_resume}'
        self._run_eval = True

    def on_validation_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called when starting validation.
        :param trainer: The current pytorch_lightning.trainer.Trainer instance.
        :param pl_module: The current pytorch_lightning.core.lightning.LightningModule instance.
        """
        if self._run_eval:
            if trainer.current_epoch == 0:
                trainer.checkpoint_connector.restore_weights()
            trainer.current_epoch = self.epoch_to_resume

    def on_validation_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called when finishing validation.
        :param trainer: the current pytorch_lightning.trainer.Trainer instance.
        :param pl_module: the current pytorch_lightning.core.lightning.LightningModule instance.
        """
        if self._run_eval:
            self._run_eval = False

    def on_test_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called when starting testing.
        :param trainer: The current pytorch_lightning.trainer.Trainer instance.
        :param pl_module: The current pytorch_lightning.core.lightning.LightningModule instance.
        """
        self.on_validation_start(trainer, pl_module)

    def on_test_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called when finishing testing.
        :param trainer: The current pytorch_lightning.trainer.Trainer instance.
        :param pl_module: The current pytorch_lightning.core.lightning.LightningModule instance.
        """
        self.on_validation_end(trainer, pl_module)

def on_test_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called when starting testing.
        :param trainer: The current pytorch_lightning.trainer.Trainer instance.
        :param pl_module: The current pytorch_lightning.core.lightning.LightningModule instance.
        """
    self.on_validation_start(trainer, pl_module)

