from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Function, Workflow, WorkflowStep
from core.utils.workflow import add_step
from ui.forms import TaskParameterTemplateForm, WorkflowStepCreateForm
from ui.views.generic import PermissionedCreateView


class WorkflowStepCreateView(PermissionedCreateView):
    """Create view for the WorkflowStep model"""

    model = WorkflowStep
    permissioned_model = "Workflow"
    environment_through_field = "workflow"
    form_class = WorkflowStepCreateForm
    template_name = WorkflowStepCreateForm.template_name

    def get_initial(self):
        """Populate initial form values"""
        initial = super().get_initial()
        initial["next"] = self.request.GET.get("next")
        initial["workflow"] = self.kwargs.get("workflow_pk")

        return initial

    def get_form_kwargs(self):
        """Setup kwargs for form instantiation"""
        kwargs = super().get_form_kwargs()
        kwargs["environment"] = self.request.session["environment_id"]

        return kwargs

    def post(self, request, workflow_pk):
        """Handle WorkflowStepForm submission"""
        # Various parent class calls require the object be set
        self.object = None

        function = Function.active_objects.get(id=self.request.POST.get("function"))
        parameter_form = TaskParameterTemplateForm(
            tasked_object=function, data=self.request.POST
        )
        step_form = self.get_form()

        if step_form.is_valid() and parameter_form.is_valid():
            step = add_step(
                **step_form.cleaned_data,
                parameter_template=parameter_form.parameter_template
            )

            success_url = reverse("ui:workflow-detail", kwargs={"pk": step.workflow.pk})

            return HttpResponseClientRedirect(success_url)
        else:
            context = self.get_context_data()
            context["parameter_form"] = parameter_form

            return render(self.request, self.template_name, context)

    def test_func(self):
        """Permission check for view access"""
        workflow = get_object_or_404(
            Workflow,
            pk=self.kwargs.get("workflow_pk"),
            environment__id=self.request.session.get("environment_id"),
        )

        return self.request.user.has_perm(
            Permission.WORKFLOW_UPDATE, workflow.environment
        )
