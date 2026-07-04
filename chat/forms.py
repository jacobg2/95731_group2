from django import forms


class QuestionForm(forms.Form):
    question = forms.CharField(
        label="Your question",
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "e.g. What are the prerequisites for 95-731?",
            }
        ),
    )
