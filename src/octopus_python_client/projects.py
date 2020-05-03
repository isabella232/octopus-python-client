import copy
import logging

from octopus_python_client.common import item_type_projects, item_type_library_variable_sets, \
    included_library_variable_set_ids_key, id_key, name_key, Common
from octopus_python_client.deployment_processes import DeploymentProcesses
from octopus_python_client.utilities.helper import find_item, compare_lists


class Projects:
    def __init__(self, config, logger=None):
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.config = config
        self.common = Common(config=config)
        self.deployment_processes = DeploymentProcesses(config=config)

    def get_all_projects(self):
        return self.common.get_one_type_save(item_type=item_type_projects)

    def get_project(self, project_literal_name):
        self.common.log_info_print(local_logger=self.logger,
                                   msg=f"get project {project_literal_name} in space {self.config.space_id}...")
        project = self.common.get_single_item_by_name_or_id_save(item_type=item_type_projects,
                                                                 item_name=project_literal_name)
        return project

    def update_project(self, project_literal_name):
        self.common.update_single_item_save(item_type=item_type_projects, item_name=project_literal_name)

    def create_project_from_local_file(self, project_literal_name=None, local_project_name=None):
        return self.common.create_single_item_from_local_file(
            item_type=item_type_projects, item_name=project_literal_name, local_item_name=local_project_name)

    def clone_project(self, project_literal_name, base_project_name):
        self.common.log_info_print(
            local_logger=self.logger,
            msg=f"clone project from {base_project_name} to {project_literal_name} inside space {self.config.space_id}")
        self.common.clone_single_item_from_remote_item(
            item_type=item_type_projects, item_name=project_literal_name, base_item_name=base_project_name)
        self.deployment_processes.clone_deployment_process(
            project_literal_name=project_literal_name, base_project_name=base_project_name)

    def delete_project(self, project_literal_name):
        self.common.log_info_print(local_logger=self.logger,
                                   msg=f"delete project {project_literal_name} in space {self.config.space_id}")
        self.common.delete_single_item_by_name_or_id(item_type=item_type_projects, item_name=project_literal_name)

    @staticmethod
    def process_suffix(name, remove_suffix, add_suffix):
        if remove_suffix and name.endswith(remove_suffix):
            name = name[:-len(remove_suffix)]
        if add_suffix:
            name += add_suffix
        return name

    def project_update_variable_sets(self, project_literal_name, remove_suffix, add_suffix):
        if not project_literal_name:
            raise ValueError("project name must not be empty")
        if not add_suffix and not remove_suffix:
            raise ValueError("add_suffix and remove_suffix can not be both empty")
        self.common.log_info_print(
            local_logger=self.logger,
            msg=f"===== updating {self.config.space_id}'s project {project_literal_name}'s variable sets by the "
                f"following operation(s)")
        if remove_suffix:
            self.common.log_info_print(local_logger=self.logger, msg=f"removing a suffix {remove_suffix}")
        if add_suffix:
            self.common.log_info_print(local_logger=self.logger, msg=f"adding a suffix {add_suffix}")

        all_variable_sets = self.common.get_one_type_ignore_error(item_type=item_type_library_variable_sets)
        library_variable_sets = self.common.get_list_items_from_all_items(all_items=all_variable_sets)
        project = self.get_project(project_literal_name)
        project_variable_sets_ids = project.get(included_library_variable_set_ids_key, [])
        self.logger.info("original variable sets id:")
        self.logger.info(project_variable_sets_ids)
        mapped_ids = copy.deepcopy(project_variable_sets_ids)
        for index, variable_sets_id in enumerate(project_variable_sets_ids):
            variable_set = find_item(lst=library_variable_sets, key=id_key, value=variable_sets_id)
            variable_set_name = variable_set.get(name_key)
            variable_set_name_updated = self.process_suffix(
                name=variable_set_name, remove_suffix=remove_suffix, add_suffix=add_suffix)
            new_variable_set_in_library_variable_sets = \
                find_item(lst=library_variable_sets, key=name_key, value=variable_set_name_updated)
            if new_variable_set_in_library_variable_sets:
                self.logger.info(f"{new_variable_set_in_library_variable_sets.get(id_key)} found in variable sets")
                mapped_ids[index] = new_variable_set_in_library_variable_sets.get(id_key)
        self.logger.info("mapped variable sets id:")
        self.logger.info(mapped_ids)
        no_change = compare_lists(project_variable_sets_ids, mapped_ids)
        if no_change:
            self.logger.info(f"The variable sets have no change")
            return project
        project[included_library_variable_set_ids_key] = mapped_ids
        return self.common.put_single_item_save(item_type=item_type_projects, payload=project)
