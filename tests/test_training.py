from support_classifier.data import load_seed_data
from support_classifier.train import train_model


def test_training_produces_predictive_artifact(tmp_path):
    result = train_model(
        load_seed_data(),
        output_path=str(tmp_path / "model.joblib"),
        c_values=(1.0,),
        use_mlflow=False,
    )
    assert result.classes == 8
    assert result.rows == 64
    assert result.accuracy >= 0.50
    assert result.macro_f1 >= 0.50
    assert (tmp_path / "model.joblib").exists()
    assert (tmp_path / "model.metrics.json").exists()

