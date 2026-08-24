# Kubeflow execution

1. Build and push `support-classifier:0.1.0` to a registry reachable by the
   Kubeflow cluster.
2. Create Kubernetes secrets/environment injection for MinIO and MLflow using
   the same variables as `docker-compose.yml`.
3. Compile with `pip install '.[kubeflow]' && python kubeflow/pipeline.py`.
4. Upload `support_pipeline.yaml` in the Kubeflow Pipelines UI and supply the
   in-cluster serving URL and quality-gate values as parameters. Before compiling,
   replace `DEFAULT_IMAGE` when using a remote registry.

The final component calls `/reload`; the stateless API instances then resolve
the `@champion` alias from the MLflow Model Registry.
