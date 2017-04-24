#include <iostream>
#include <libgearman/gearman.h>
#include <libgearman-server/config.h>

int main() {
	gearman_worker_st *worker = gearman_worker_create(nullptr);
	gearman_worker_free(worker);

	gearmand_config_st *conf = gearmand_config_create();
	gearmand_config_free(conf);
}
