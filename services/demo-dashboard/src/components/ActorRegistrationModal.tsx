import { useState } from 'react';
import { Modal, TextInput, Select, Button, Stack, MultiSelect, Group } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconUserPlus } from '@tabler/icons-react';
import { registerActor } from '../services/api';
import type { ActorRegistration } from '../types';

interface ActorRegistrationModalProps {
    opened: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export function ActorRegistrationModal({ opened, onClose, onSuccess }: ActorRegistrationModalProps) {
    const [loading, setLoading] = useState(false);

    const form = useForm<ActorRegistration>({
        initialValues: {
            name: '',
            actorType: 'PSP',
            countryCode: '',
            bic: '',
            callbackUrl: '',
            supportedCurrencies: [],
        },
        validate: {
            name: (value) => (value.length < 2 ? 'Name must be at least 2 characters' : null),
            countryCode: (value) => (value.length !== 2 ? 'Country code must be 2 characters' : null),
            bic: (value) => (/^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$/.test(value) ? null : 'Invalid BIC format'),
        },
    });

    const handleSubmit = async (values: ActorRegistration) => {
        setLoading(true);
        try {
            await registerActor(values);
            notifications.show({
                title: 'Actor Registered',
                message: `${values.name} has been added to the registry`,
                color: 'green',
            });
            onSuccess?.();
            onClose();
            form.reset();
        } catch (err) {
            notifications.show({
                title: 'Registration Failed',
                message: err instanceof Error ? err.message : 'Unknown error',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal opened={opened} onClose={onClose} title="Register New Actor">
            <form onSubmit={form.onSubmit(handleSubmit)}>
                <Stack>
                    <TextInput
                        label="Entity Name"
                        placeholder="e.g. Acme Payments Ltd"
                        required
                        {...form.getInputProps('name')}
                    />

                    <Select
                        label="Actor Type"
                        data={[
                            { value: 'PSP', label: 'Payment Service Provider (PSP)' },
                            { value: 'IPS', label: 'Instant Payment System (IPS)' },
                            { value: 'FXP', label: 'FX Provider (FXP)' },
                            { value: 'SAP', label: 'Settlement Access Provider (SAP)' },
                            { value: 'PDO', label: 'Proxy Directory Operator (PDO)' },
                        ]}
                        required
                        {...form.getInputProps('actorType')}
                    />

                    <Group grow>
                        <TextInput
                            label="Country Code"
                            placeholder="SG"
                            maxLength={2}
                            required
                            {...form.getInputProps('countryCode')}
                            onChange={(e) => form.setFieldValue('countryCode', e.target.value.toUpperCase())}
                        />
                        <TextInput
                            label="BIC"
                            placeholder="BANKUS33"
                            maxLength={11}
                            required
                            {...form.getInputProps('bic')}
                            onChange={(e) => form.setFieldValue('bic', e.target.value.toUpperCase())}
                        />
                    </Group>

                    <TextInput
                        label="Callback URL"
                        placeholder="https://api.example.com/nexus/callback"
                        {...form.getInputProps('callbackUrl')}
                    />

                    <MultiSelect
                        label="Supported Currencies"
                        data={['SGD', 'IDR', 'THB', 'MYR', 'PHP', 'INR', 'USD', 'EUR']}
                        placeholder="Select currencies"
                        {...form.getInputProps('supportedCurrencies')}
                    />

                    <Group justify="flex-end" mt="md">
                        <Button variant="default" onClick={onClose}>Cancel</Button>
                        <Button type="submit" loading={loading} leftSection={<IconUserPlus size={16} />}>
                            Register
                        </Button>
                    </Group>
                </Stack>
            </form>
        </Modal>
    );
}
