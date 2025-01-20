locals {
  project_ids = {
    dev = var.dev_project_id
  }
}


# Get the project number for the dev project
data "google_project" "dev_project" {
  project_id = var.dev_project_id
}

# Grant Storage Object Creator role to default compute service account
resource "google_project_iam_member" "default_compute_sa_storage_object_creator" {
  project    = var.dev_project_id
  role       = "roles/cloudbuild.builds.builder"
  member     = "serviceAccount:${data.google_project.dev_project.number}-compute@developer.gserviceaccount.com"
  depends_on = [resource.google_project_service.services]
}


# Grant required permissions to Vertex AI service account
resource "google_project_iam_member" "vertex_ai_sa_permissions" {
  for_each = {
    for pair in setproduct(keys(local.project_ids), var.agentengine_sa_roles) :
    join(",", pair) => {
      project = local.project_ids[pair[0]]
      role    = pair[1]
    }
  }

  project = var.dev_project_id
  role    = each.value
  member  = "serviceAccount:service-${data.google_project.dev_project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  depends_on = [resource.google_project_service.services]
}
