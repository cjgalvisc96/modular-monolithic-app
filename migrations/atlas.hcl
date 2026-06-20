// Atlas configuration for schema migrations.
// Apply with:  atlas migrate apply --env local
// New diff:    atlas migrate diff <name> --env local

variable "db_url" {
  type    = string
  default = getenv("ATLAS_DB_URL")
}

env "local" {
  url     = var.db_url != "" ? var.db_url : "postgres://todo:todo@localhost:5432/todo?sslmode=disable"
  dev     = "docker://postgres/16/dev?search_path=public"
  migration {
    dir = "file://versions"
  }
  format {
    migrate {
      apply = "{{ json . }}"
    }
  }
}

env "dev" {
  url = getenv("ATLAS_DB_URL")
  migration {
    dir = "file://versions"
  }
}

env "prod" {
  url = getenv("ATLAS_DB_URL")
  migration {
    dir = "file://versions"
  }
}
