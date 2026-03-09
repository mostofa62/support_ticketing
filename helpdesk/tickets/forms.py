# tickets/forms.py
from django import forms
from ict_support.models import Ticket, IssueCategory, IssueSubcategory

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        #fields = ['category', 'subcategory', 'priority', 'location', 'description']
        fields = ['category', 'subcategory', 'location', 'description']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially, no subcategories
        self.fields['subcategory'].queryset = IssueSubcategory.objects.none()

        if 'category' in self.data:
            # When submitting the form (POST), filter subcategories for the selected category
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = IssueSubcategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass  # invalid input from user
        elif self.instance.pk:
            # When editing an existing Ticket, show its subcategories
            self.fields['subcategory'].queryset = IssueSubcategory.objects.filter(category=self.instance.category)

        # Apply Bootstrap classes and placeholders to widgets for better layout
        widget_map = {
            'category': ('form-select', ''),
            'subcategory': ('form-select', ''),
            #'priority': ('form-select', ''),
            'location': ('form-control', 'Location (building/room)'),
            'description': ('form-control', 'Describe the issue in detail'),
        }

        for name, (css, placeholder) in widget_map.items():
            if name in self.fields:
                w = self.fields[name].widget
                existing = w.attrs.get('class', '')
                w.attrs.update({
                    'class': (existing + ' ' + css).strip(),
                })
                if placeholder:
                    w.attrs.update({'placeholder': placeholder})
